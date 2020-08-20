import base64
import logging
import functools
import json
import os
import re
import shutil
from time import sleep

import click
import pytesseract
import requests
from PIL import Image
from bs4 import BeautifulSoup
from lxml import etree

# Disable requests warnings for things like disabling certificate checking
requests.packages.urllib3.disable_warnings()


class DomainReview(object):
    """Class to pull a list of registered domains belonging to a Namecheap account and then check
    the web reputation of each domain.
    """
    # Confluence markup colors -- *s make bold text
    color_end = r"*{color}"
    red_text = r"{color:red}*"
    green_text = r"{color:green}*"
    orange_text = r"{color:orange}*"
    # API endpoints
    malwaredomains_url = 'http://mirror1.malwaredomains.com/files/justdomains'
    virustotal_domain_report_uri = 'https://www.virustotal.com/vtapi/v2/domain/report?apikey={}&domain={}'
    get_domain_list_endpoint = 'https://api.namecheap.com/xml.response?ApiUser={}&ApiKey={}&UserName={}&Command=namecheap.domains.getList&ClientIp={}&PageSize={}'
    get_dns_list_endpoint = 'https://api.namecheap.com/xml.response?ApiUser={}&ApiKey={}&UserName={}&Command=namecheap.domains.dns.getHosts&ClientIp={}&SLD={}&TLD={}'
    # Categories we don't want to see
    # These are lowercase to avoid inconsistencies with how each service might return the categories
    blacklisted = ['phishing', 'web ads/analytics', 'suspicious', 'shopping', 'placeholders',
                   'pornography', 'spam', 'gambling', 'scam/questionable/illegal',
                   'malicious sources/malnets']
    # Variables for web browsing
    useragent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'
    session = requests.Session()
    session.request = functools.partial(session.request, timeout=20)

    # Additional settings
    request_delay = 20

    def __init__(self, virustotal_api_key):
        """Everything that needs to be setup when a new DomainReview object is created goes here."""
        try:
            self.virustotal_api_key = virustotal_api_key
        except Exception as error:
            click.secho('[!] Could not load all necessary API information from the domaincheck.config.', fg='red')
            click.secho('L.. Details: {}'.format(error), fg='red')
            exit()

    def check_virustotal(self, domain, ignore_case=False):
        """Check the provided domain name with VirusTotal. VirusTotal's API is case sensitive, so
        the domain will be converted to lowercase by default. This can be disabled using the
        ignore_case parameter.
        This uses the VirusTotal /domain/report endpoint:
        https://developers.virustotal.com/v2.0/reference#domain-report
        """
        if not ignore_case:
            domain = domain.lower()
        req = self.session.get(self.virustotal_domain_report_uri.format(self.virustotal_api_key, domain))
        try:
            vt_data = req.json()
        except Exception as e:
            logging.error(e)
            vt_data = {}

        return vt_data

    def check_talos(self, domain):
        """Check the provided domain's category as determined by Cisco Talos."""
        categories = []
        cisco_talos_uri = 'https://talosintelligence.com/sb_api/query_lookup?query=%2Fapi%2Fv2%2Fdetails%2Fdomain%2F&query_entry={}&offset=0&order=ip+asc'
        headers = {'User-Agent': self.useragent,
                   'Referer': 'https://www.talosintelligence.com/reputation_center/lookup?search=' + domain}
        try:
            req = self.session.get(cisco_talos_uri.format(domain), headers=headers)
            if req.ok:
                json_data = req.json()
                category = json_data['category']
                if category:
                    categories.append(json_data['category']['description'])
                else:
                    categories.append('Uncategorized')
            else:
                click.secho('\n[!] Cisco Talos check request failed. Talos did not return a 200 response.', fg='red')
                click.secho('L.. Request returned status "{}"'.format(req.status_code), fg='red')
        except Exception as error:
            click.secho('\n[!] Cisco Talos request failed: {}'.format(error), fg='red')
        return categories

    def check_ibm_xforce(self, domain):
        """Check the provided domain's category as determined by IBM X-Force."""
        categories = []
        xforce_uri = 'https://exchange.xforce.ibmcloud.com/url/{}'.format(domain)
        headers = {'User-Agent': self.useragent,
                   'Accept': 'application/json, text/plain, */*',
                   'x-ui': 'XFE',
                   'Origin': xforce_uri,
                   'Referer': xforce_uri}
        xforce_api_uri = 'https://api.xforce.ibmcloud.com/url/{}'.format(domain)
        try:
            req = self.session.get(xforce_api_uri, headers=headers, verify=False)
            if req.ok:
                response = req.json()
                if not response['result']['cats']:
                    categories.append('Uncategorized')
                else:
                    temp = ''
                    # Parse all dictionary keys and append to single string to get Category names
                    for key in response['result']['cats']:
                        categories.append(key)
                    # categories = "{0}(Score: {1})".format(temp, str(response['result']['score']))
            # IBM X-Force returns a 404 with {"error":"Not found."} if the domain is unknown
            elif req.status_code == 404:
                categories.append('Unknown')
            else:
                click.secho('\n[!] IBM X-Force check request failed. X-Force did not return a 200 response.', fg='red')
                click.secho('L.. Request returned status "{}"'.format(req.status_code), fg='red')
        except Exception as error:
            click.secho('\n[!] IBM X-Force request failed: {}'.format(error), fg='red')
        return categories

    def check_fortiguard(self, domain):
        """Check the provided domain's category as determined by Fortiguard Webfilter."""
        categories = []
        fortiguard_uri = 'https://fortiguard.com/webfilter?q=' + domain
        headers = {'User-Agent': self.useragent,
                   'Origin': 'https://fortiguard.com',
                   'Referer': 'https://fortiguard.com/webfilter'}
        try:
            req = self.session.get(fortiguard_uri, headers=headers)
            if req.ok:
                """
                Example HTML result:
                <div class="well">
                    <div class="row">
                        <div class="col-md-9 col-sm-12">
                            <h4 class="info_title">Category: Education</h4>
                """
                # TODO: Might be best to BS4 for this rather than regex
                cat = re.findall('Category: (.*?)" />', req.text, re.DOTALL)
                categories.append(cat[0])
            else:
                click.secho('\n[!] Fortiguard check request failed. Fortiguard did not return a 200 response.',
                            fg='red')
                click.secho('L.. Request returned status "{}"'.format(req.status_code), fg='red')
        except Exception as error:
            click.secho('\n[!] Fortiguard request failed: {}'.format(error), fg='red')
        return categories

    def check_bluecoat(self, domain, ocr=True):
        """Check the provided domain's category as determined by Symantec Bluecoat."""
        categories = []
        bluecoart_uri = 'https://sitereview.bluecoat.com/resource/lookup'
        post_data = {'url': domain, 'captcha': ''}
        headers = {'User-Agent': self.useragent,
                   'Content-Type': 'application/json; charset=UTF-8',
                   'Referer': 'https://sitereview.bluecoat.com/lookup'}
        try:
            response = self.session.post(bluecoart_uri, headers=headers, json=post_data, verify=False)
            root = etree.fromstring(response.text)
            for node in root.xpath("//CategorizationResult//categorization//categorization//name"):
                categories.append(node.text)
            if 'captcha' in categories:
                if ocr:
                    # This request is also performed by a browser, but is not needed for our purposes
                    click.secho('[*] Received a CAPTCHA challenge from Bluecoat...', fg='yellow')
                    captcha = self.solve_captcha('https://sitereview.bluecoat.com/resource/captcha.jpg', self.session)
                    if captcha:
                        b64captcha = base64.urlsafe_b64encode(captcha.encode('utf-8')).decode('utf-8')
                        # Send CAPTCHA solution via GET since inclusion with the domain categorization request doesn't work anymore
                        click.secho('[*] Submitting an OCRed CAPTCHA text to Bluecoat...', fg='yellow')
                        captcha_solution_url = 'https://sitereview.bluecoat.com/resource/captcha-request/{0}'.format(
                            b64captcha)
                        response = self.session.get(url=captcha_solution_url, headers=headers, verify=False)
                        # Try the categorization request again
                        response = self.session.post(bluecoart_uri, headers=headers, json=post_data, verify=False)
                        response_json = json.loads(response.text)
                        if 'errorType' in response_json:
                            click.secho('[!] CAPTCHA submission was apparently incorrect!', fg='red')
                            categories = response_json['errorType']
                        else:
                            click.secho('[!] CAPTCHA submission was accepted!', fg='green')
                            categories = response_json['categorization'][0]['name']
                    else:
                        click.secho(
                            '\n[!] Failed to solve BlueCoat CAPTCHA with OCR. Manually solve at: "https://sitereview.bluecoat.com/sitereview.jsp"',
                            fg='red')
                else:
                    click.secho(
                        '\n[!] Failed to solve BlueCoat CAPTCHA with OCR. Manually solve at: "https://sitereview.bluecoat.com/sitereview.jsp"',
                        fg='red')
        except Exception as error:
            click.secho('\n[!] Bluecoat request failed: {0}'.format(error), fg='red')
        return categories

    def solve_captcha(self, url, session):
        """Solve a Bluecoat CAPTCHA for the provided session."""
        # Downloads CAPTCHA image and saves to current directory for OCR with tesseract
        # Returns CAPTCHA string or False if error occurred
        jpeg = 'captcha.jpg'
        headers = {'User-Agent': self.useragent}
        try:
            response = session.get(url=url, headers=headers, verify=False, stream=True)
            if response.status_code == 200:
                with open(jpeg, 'wb') as f:
                    response.raw.decode_content = True
                    shutil.copyfileobj(response.raw, f)
            else:
                click.secho('[!] Failed to download the Bluecoat CAPTCHA.', fg='red')
                return False
            # Perform basic OCR without additional image enhancement
            text = pytesseract.image_to_string(Image.open(jpeg))
            text = text.replace(" ', '").replace("[', 'l").replace("'', '")
            # Remove CAPTCHA file
            try:
                os.remove(jpeg)
            except OSError:
                pass
            return text
        except Exception as error:
            click.secho('[!] Error processing the Bluecoat CAPTCHA.'.format(error), fg='red')
            return False

    def check_mxtoolbox(self, domain):
        """Check if the provided domain is blacklisted as spam as determined by MX Toolkit."""
        issues = []
        mxtoolbox_url = 'https://mxtoolbox.com/Public/Tools/BrandReputation.aspx'
        headers = {'User-Agent': self.useragent,
                   'Origin': mxtoolbox_url,
                   'Referer': mxtoolbox_url}
        try:
            response = self.session.get(url=mxtoolbox_url, headers=headers)
            soup = BeautifulSoup(response.content, 'lxml')
            viewstate = soup.select('input[name=__VIEWSTATE]')[0]['value']
            viewstategenerator = soup.select('input[name=__VIEWSTATEGENERATOR]')[0]['value']
            eventvalidation = soup.select('input[name=__EVENTVALIDATION]')[0]['value']
            data = {
                '__EVENTTARGET': '',
                '__EVENTARGUMENT': '',
                '__VIEWSTATE': viewstate,
                '__VIEWSTATEGENERATOR': viewstategenerator,
                '__EVENTVALIDATION': eventvalidation,
                'ctl00$ContentPlaceHolder1$brandReputationUrl': domain,
                'ctl00$ContentPlaceHolder1$brandReputationDoLookup': 'Brand Reputation Lookup',
                'ctl00$ucSignIn$hfRegCode': 'missing',
                'ctl00$ucSignIn$hfRedirectSignUp': '/Public/Tools/BrandReputation.aspx',
                'ctl00$ucSignIn$hfRedirectLogin': '',
                'ctl00$ucSignIn$txtEmailAddress': '',
                'ctl00$ucSignIn$cbNewAccount': 'cbNewAccount',
                'ctl00$ucSignIn$txtFullName': '',
                'ctl00$ucSignIn$txtModalNewPassword': '',
                'ctl00$ucSignIn$txtPhone': '',
                'ctl00$ucSignIn$txtCompanyName': '',
                'ctl00$ucSignIn$drpTitle': '',
                'ctl00$ucSignIn$txtTitleName': '',
                'ctl00$ucSignIn$txtModalPassword': ''
            }
            response = self.session.post(url=mxtoolbox_url, headers=headers, data=data)
            soup = BeautifulSoup(response.content, 'lxml')
            if soup.select('div[id=ctl00_ContentPlaceHolder1_noIssuesFound]'):
                issues.append('No issues found')
            else:
                if soup.select('div[id=ctl00_ContentPlaceHolder1_googleSafeBrowsingIssuesFound]'):
                    issues.append('Google SafeBrowsing Issues Found.')
                if soup.select('div[id=ctl00_ContentPlaceHolder1_phishTankIssuesFound]'):
                    issues.append('PhishTank Issues Found')
        except Exception as error:
            click.secho('\n[!] Error retrieving Google SafeBrowsing and PhishTank reputation!', fg='red')
        return issues

    def check_cymon(self, target):
        """Get reputation data from Cymon.io for target IP address. This returns two dictionaries
        for domains and security events.
        A Cymon API key is not required, but is recommended.
        """
        try:
            req = self.session.get(url='https://cymon.io/' + target, verify=False)
            if req.status_code == 200:
                if 'IP Not Found' in req.text:
                    return False
                else:
                    return True
            else:
                return False
        except Exception:
            return False

    def check_opendns(self, domain):
        """Check the provided domain's category as determined by the OpenDNS community."""
        categories = []
        opendns_uri = 'https://domain.opendns.com/{}'
        headers = {'User-Agent': self.useragent}
        try:
            response = self.session.get(opendns_uri.format(domain), headers=headers, verify=False)
            soup = BeautifulSoup(response.content, 'lxml')
            tags = soup.find('span', {'class': 'normal'})
            if tags:
                categories = tags.text.strip().split(', ')
            else:
                categories.append('No Tags')
        except Exception as error:
            click.secho('\n[!] OpenDNS request failed: {0}'.format(error), fg='red')
        return categories

    def check_trendmicro(self, domain):
        """Check the provided domain's category as determined by the Trend Micro."""
        categories = []
        trendmicro_uri = 'https://global.sitesafety.trendmicro.com/'
        trendmicro_stage_1_uri = 'https://global.sitesafety.trendmicro.com/lib/idn.php'
        trendmicro_stage_2_uri = 'https://global.sitesafety.trendmicro.com/result.php'
        headers = {'User-Agent': self.useragent}
        headers_stage_1 = {
            'Host': 'global.sitesafety.trendmicro.com',
            'Accept': '*/*',
            'Origin': 'https://global.sitesafety.trendmicro.com',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': self.useragent,
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': 'https://global.sitesafety.trendmicro.com/index.php',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-US, en;q=0.9'
        }
        headers_stage_2 = {
            'Origin': 'https://global.sitesafety.trendmicro.com',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': self.useragent,
            'Accept': 'text/html, application/xhtml+xml, application/xml;q=0.9, image/webp, image/apng, */*;q=0.8',
            'Referer': 'https://global.sitesafety.trendmicro.com/index.php',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-US, en;q=0.9'
        }
        data_stage_1 = {'url': domain}
        data_stage_2 = {'urlname': domain,
                        'getinfo': 'Check Now'
                        }
        try:
            response = self.session.get(trendmicro_uri, headers=headers)
            response = self.session.post(trendmicro_stage_1_uri, headers=headers_stage_1, data=data_stage_1)
            response = self.session.post(trendmicro_stage_2_uri, headers=headers_stage_2, data=data_stage_2)
            # Check if session was redirected to /captcha.php
            if 'captcha' in response.url:
                click.secho('[!] TrendMicro responded with a reCAPTCHA, so cannot proceed with TrendMicro.', fg='red')
                click.secho('L.. You can try solving it yourself: https://global.sitesafety.trendmicro.com/captcha.php',
                            fg='red')
            else:
                soup = BeautifulSoup(response.content, 'lxml')
                tags = soup.find('div', {'class': 'labeltitlesmallresult'})
                if tags:
                    categories = tags.text.strip().split(', ')
                else:
                    categories.append('Uncategorized')
        except Exception as error:
            click.secho('\n[!] Trend Micro request failed: {0}'.format(error), fg='red')
        return categories

    def download_malware_domains(self):
        """Downloads the malwaredomains.com list of malicious domains."""
        headers = {'User-Agent': self.useragent}
        response = self.session.get(url=self.malwaredomains_url, headers=headers, verify=False)
        malware_domains = response.text
        if response.status_code == 200:
            return malware_domains
        else:
            click.secho('[!] Error reaching: {}, Status: {}'.format(self.malwaredomains_url, response.status_code),
                        fg='red')
            return None

    def check_domain_status(self, domains_list, filter_list=None):
        """Check the status of each domain in the provided list collected from Namecheap's domainList
        API. Each domain will be checked to ensure WHOIS privacy is enabled, the domain has not expired,
        and the domain is not flagged/blacklisted. A domain will be considered burned if VirusTotal
        returns detections for the domain or one of the domain's categories appears in the list of
        bad categories.
        VirusTotal allows 4 requests every 1 minute, so a minimum of sleep(20) is recommended.
        """
        if filter_list:
            num_of_domains = len(filter_list)
        else:
            num_of_domains = len(domains_list)
        lab_results = {}
        malware_domains = self.download_malware_domains()
        with click.progressbar(domains_list,
                               label='Checking domains',
                               length=num_of_domains) as bar:
            for item in bar:
                domain = item['Name']
                creation_date = item['Created']
                expiration_date = item['Expires']
                domain_categories = []
                burned_explanations = []
                # If there's a filter list, continue past any domain not in it
                if filter_list:
                    if not domain in filter_list:
                        continue
                # Default values: Healthy until proven burned
                burned = False
                burned_dns = False
                health = 'Healthy'
                health_dns = 'Healthy'
                whoisguard = 'Enabled'
                expired = 'False'
                # Check the Namecheap status of the domain
                if not item['WhoisGuard'].lower() == 'enabled':
                    whoisguard = item['WhoisGuard'].upper()
                else:
                    expired = 'Enabled'
                if not item['IsExpired'].lower() == 'False':
                    expired = item['IsExpired'].upper()
                else:
                    expired = 'False'
                # Check if domain is flagged for malware
                if malware_domains:
                    if domain in malware_domains:
                        click.secho(
                            '\n[!] {}: Identified as a known malware domain (malwaredomains.com)!'.format(domain),
                            fg='red')
                        burned = True
                        health = 'Burned'
                        burned_explanations.append('Flagged by malwaredomains.com')
                # Check domain name with VirusTotal
                vt_results = self.check_virustotal(item['Name'])
                if 'categories' in vt_results:
                    domain_categories = vt_results['categories']
                # Check if VirusTotal has any detections for URLs or samples
                if 'detected_downloaded_samples' in vt_results:
                    if len(vt_results['detected_downloaded_samples']) > 0:
                        click.secho('\n[!] {}: Identified as having a downloaded sample on VirusTotal!'.format(domain),
                                    fg='red')
                        burned = True
                        health = 'Burned'
                        burned_explanations.append('Tied to a VirusTotal detected malware sample')
                if 'detected_urls' in vt_results:
                    if len(vt_results['detected_urls']) > 0:
                        click.secho('\n[!] {}: Identified as having a URL detection on VirusTotal!'.format(domain),
                                    fg='red')
                        burned = True
                        health = 'Burned'
                        burned_explanations.append('Tied to a VirusTotal detected URL')
                # Get passive DNS results from VirusTotal JSON
                ip_addresses = []
                if 'resolutions' in vt_results:
                    for address in vt_results['resolutions']:
                        ip_addresses.append(
                            {'address': address['ip_address'], 'timestamp': address['last_resolved'].split(" ")[0]})
                bad_addresses = []
                for address in ip_addresses:
                    if self.check_cymon(address['address']):
                        burned_dns = True
                        bad_addresses.append(address['address'] + '/' + address['timestamp'])
                if burned_dns:
                    click.secho(
                        '\n[*] {}: Identified as pointing to suspect IP addresses (VirusTotal passive DNS).'.format(
                            domain), fg='yellow')
                    health_dns = 'Flagged DNS ({})'.format(', '.join(bad_addresses))
                # Collect categories from the other sources
                xforce_results = self.check_ibm_xforce(domain)
                domain_categories.extend(xforce_results)
                talos_results = self.check_talos(domain)
                domain_categories.extend(talos_results)
                bluecoat_results = self.check_bluecoat(domain)
                domain_categories.extend(bluecoat_results)
                fortiguard_results = self.check_fortiguard(domain)
                domain_categories.extend(fortiguard_results)
                opendns_results = self.check_opendns(domain)
                domain_categories.extend(opendns_results)
                trendmicro_results = self.check_trendmicro(domain)
                domain_categories.extend(trendmicro_results)
                mxtoolbox_results = self.check_mxtoolbox(domain)
                domain_categories.extend(domain_categories)
                # Make categories unique
                domain_categories = list(set(domain_categories))
                # Check if any categopries are suspect
                bad_cats = []
                for category in domain_categories:
                    if category.lower() in self.blacklisted:
                        bad_cats.append(category.capitalize())
                if bad_cats:
                    click.secho('\n[!] {}: is tagged with a bad category, {}!'.format(domain, ', '.join(bad_cats)),
                                fg='red')
                    burned = True
                    health = 'Burned'
                    burned_explanations.append('Tagged with a bad category')
                # Collect the DNS records
                dns_records = []
                namecheap_records = self.get_domain_dns_namecheap(domain)
                if namecheap_records[domain]['Status'] == 'OK':
                    for key, value in namecheap_records[domain]['Records'].items():
                        dns_records.append('{} {}'.format(key, value))
                # Assemble the dictionary to return for this domain
                lab_results[domain] = {}
                lab_results[domain]['dns'] = {}
                lab_results[domain]['categories'] = {}
                lab_results[domain]['health'] = health
                lab_results[domain]['burned_explanation'] = ', '.join(burned_explanations)
                lab_results[domain]['health_dns'] = health_dns
                lab_results[domain]['creation'] = creation_date
                lab_results[domain]['expiration'] = expiration_date
                lab_results[domain]['expired'] = expired
                lab_results[domain]['whoisguard'] = whoisguard
                lab_results[domain]['categories']['all'] = domain_categories
                lab_results[domain]['categories']['talos'] = talos_results
                lab_results[domain]['categories']['xforce'] = xforce_results
                lab_results[domain]['categories']['opendns'] = opendns_results
                lab_results[domain]['categories']['bluecoat'] = bluecoat_results
                lab_results[domain]['categories']['mxtoolbox'] = mxtoolbox_results
                lab_results[domain]['categories']['trendmicro'] = trendmicro_results
                lab_results[domain]['categories']['fortiguard'] = fortiguard_results
                lab_results[domain]['dns'] = dns_records
                # Sleep for a while for VirusTotal's API
                sleep(self.request_delay)
        return lab_results


def review_domain(domain, vt_token):
    lab_results = {}
    domain_categories = []
    burned_explanations = []
    burned_dns = False
    health = 'Healthy'
    health_dns = 'Healthy'
    dr = DomainReview(vt_token)
    malware_domains = dr.download_malware_domains()

    # Check if domain is flagged for malware
    if malware_domains:
        if domain in malware_domains:
            health = 'Burned'
            burned_explanations.append('Flagged by malwaredomains.com')

    # Check domain name with VirusTotal
    vt_results = dr.check_virustotal(domain)
    if 'categories' in vt_results:
        domain_categories = vt_results['categories']

    # Check if VirusTotal has any detections for URLs or samples
    if 'detected_downloaded_samples' in vt_results:
        if len(vt_results['detected_downloaded_samples']) > 0:
            health = 'Burned'
            burned_explanations.append('Tied to a VirusTotal detected malware sample')
    if 'detected_urls' in vt_results:
        if len(vt_results['detected_urls']) > 0:
            health = 'Burned'
            burned_explanations.append('Tied to a VirusTotal detected URL')

    # Get passive DNS results from VirusTotal JSON
    ip_addresses = []
    if 'resolutions' in vt_results:
        for address in vt_results['resolutions']:
            ip_addresses.append(
                {'address': address['ip_address'], 'timestamp': address['last_resolved'].split(" ")[0]})
    bad_addresses = []
    for address in ip_addresses:
        if dr.check_cymon(address['address']):
            burned_dns = True
            bad_addresses.append(address['address'] + '/' + address['timestamp'])
    if burned_dns:
        health_dns = 'Flagged DNS ({})'.format(', '.join(bad_addresses))

    # Collect categories from the other sources
    xforce_results = dr.check_ibm_xforce(domain)
    domain_categories.extend(xforce_results)

    talos_results = dr.check_talos(domain)
    domain_categories.extend(talos_results)

    bluecoat_results = dr.check_bluecoat(domain)
    domain_categories.extend(bluecoat_results)

    fortiguard_results = dr.check_fortiguard(domain)
    domain_categories.extend(fortiguard_results)

    opendns_results = dr.check_opendns(domain)
    domain_categories.extend(opendns_results)

    trendmicro_results = dr.check_trendmicro(domain)
    domain_categories.extend(trendmicro_results)

    mxtoolbox_results = dr.check_mxtoolbox(domain)
    domain_categories.extend(domain_categories)

    # Make categories unique
    domain_categories = list(set(domain_categories))
    # Check if any categopries are suspect
    bad_cats = []
    for category in domain_categories:
        if category.lower() in DomainReview.blacklisted:
            bad_cats.append(category.capitalize())
    if bad_cats:
        health = 'Burned'
        burned_explanations.append('Tagged with a bad category')

    # Assemble the dictionary to return for this domain
    lab_results[domain] = {}
    lab_results[domain]['categories'] = {}

    lab_results[domain]['health'] = health
    lab_results[domain]['burned_explanation'] = ', '.join(burned_explanations)
    lab_results[domain]['health_dns'] = health_dns

    # lab_results[domain]['categories']['all'] = domain_categories
    lab_results[domain]['categories']['talos'] = talos_results
    lab_results[domain]['categories']['xforce'] = xforce_results
    lab_results[domain]['categories']['opendns'] = opendns_results
    lab_results[domain]['categories']['bluecoat'] = bluecoat_results
    lab_results[domain]['categories']['mxtoolbox'] = mxtoolbox_results
    lab_results[domain]['categories']['trendmicro'] = trendmicro_results
    lab_results[domain]['categories']['fortiguard'] = fortiguard_results

    # return lab_results[domain]
    return dict(
        health=health,
        burned_explanation=', '.join(burned_explanations),
        health_dns=health_dns,
        **lab_results[domain]['categories']
    )