import logging
from abc import ABC
from abc import abstractmethod
from typing import List

import digitalocean
from namesilo.core import NameSilo
from vultr import Vultr
from vultr import VultrError

from app.schemas import vps as vps_schema
from utils.terraform import Terraform
from utils.tools import gen_ssh_key_fingerprint


class BaseIsp(ABC):
    def __init__(self, api_token, *args, **kwargs):
        self.api_token = api_token

        # set isp obj
        self.isp = self.get_isp_obj(*args, **kwargs)

    @abstractmethod
    def get_isp_obj(self, *args, **kwargs):
        pass

    @property
    @abstractmethod
    def api_url(self):
        pass


class BaseDomainIsp(BaseIsp):
    def __init__(self, api_token, *args, **kwargs):
        super().__init__(api_token, *args, **kwargs)

    @abstractmethod
    def get_isp_obj(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_domain_info(self, domain_name):
        pass

    @abstractmethod
    def check_domain(self, domain_name):
        pass

    @abstractmethod
    def list_dns_records(self, domain_name):
        pass

    @abstractmethod
    def register_domain(self, domain_name: str, years=1, auto_renew=0, private=0) -> bool:
        pass

    @abstractmethod
    def set_dns_a_record(self, domain_name: str, ip: str) -> bool:
        pass


class NameSiloIsp(BaseDomainIsp):
    def get_isp_obj(self, *args, **kwargs):
        return NameSilo(self.api_token, sandbox=kwargs.get('is_test'))

    def get_domain_info(self, domain_name):
        return self.isp.get_domain_info(domain_name)

    def check_domain(self, domain_name):
        return self.isp.check_domain(domain_name)

    def check_domain_raw(self, domain_name):
        url_extend = f"checkRegisterAvailability?version=1&type=xml&" \
                     f"key={self.api_token}&domains={domain_name}"
        parsed_content = self.isp._process_data(url_extend)
        return parsed_content.get('namesilo')

    def get_prices(self):
        return self.isp.get_prices()

    def list_dns_records(self, domain_name):
        """
        List dns records for specified domain name
        :param domain_name:
        :return: current domain's dns record
        :rtype: List
        """
        url_extend = "dnsListRecords?version=1&type=xml&key=%s&domain=%s" % (self.api_token, domain_name)
        parsed_context = self.isp._process_data(url_extend)
        resource_record = parsed_context['namesilo']['reply']['resource_record']

        result = []

        if isinstance(resource_record, list):
            result.extend(resource_record)
        else:
            result.append(resource_record)
        return result

    def register_domain(self, domain_name: str, years=1, auto_renew=0, private=1) -> bool:
        return self.isp.register_domain(domain_name, years, auto_renew, private)

    def list_domain_dns_records(self, domain_name: str):
        url_extend = "dnsListRecords?version=1&type=xml&key=%s&domain=%s&rrtype=A" % (
            self.api_token, domain_name
        )
        parsed_context = self.isp._process_data(url_extend)
        return parsed_context

    def set_dns_a_record(self, domain_name: str, ip: str) -> bool:
        url_extend = "dnsAddRecord?version=1&type=xml&key=%s&domain=%s&rrtype=A&rrvalue=%s" % (
            self.api_token, domain_name, ip
        )
        parsed_context = self.isp._process_data(url_extend)
        detail = parsed_context['namesilo']['reply'].get('detail')
        return detail == 'success'

    @property
    def api_url(self):
        return self.isp._base_url


class BaseVpsIsp(BaseIsp):
    @abstractmethod
    def get_isp_obj(self, *args, **kwargs):
        pass

    @abstractmethod
    def is_valid_account(self) -> bool:
        pass

    @abstractmethod
    def create_ssh_key(self, name: str, public_key_content: str) -> str:
        pass

    @abstractmethod
    def get_available_os_list(self):
        pass

    @abstractmethod
    def get_available_plans_list(self):
        pass

    @abstractmethod
    def get_available_regions_list(self):
        pass

    @abstractmethod
    def get_ssh_key_list(self, vps_isp_id: int) -> List[dict]:
        pass

    @abstractmethod
    def destroy_ssh_key(self, ssh_key_id):
        pass

    @abstractmethod
    def create_server(self, vps_profile: dict, public_key: str = None, *args, **kwargs) -> dict:
        pass

    @abstractmethod
    def start_server(self, server_id, *args, **kwargs) -> bool:
        pass

    @abstractmethod
    def reboot_server(self, server_id, *args, **kwargs) -> bool:
        pass

    @abstractmethod
    def shutdown_server(self, server_id, *args, **kwargs) -> bool:
        pass

    @abstractmethod
    def reinstall_server(self, server_id, *args, **kwargs) -> bool:
        pass

    @abstractmethod
    def destroy_server(self, server_id, *args, **kwargs) -> bool:
        pass


class VultrIsp(BaseVpsIsp):
    def get_isp_obj(self, **kwargs: dict):
        return Vultr(self.api_token)

    def is_valid_account(self):
        valid = True
        try:
            self.isp.account.info()
        except:
            valid = False
        finally:
            return valid

    def create_ssh_key(self, name: str, public_key_content: str) -> str:
        isp_ssh_key_data = self.isp.sshkey.create(name, public_key_content)
        return isp_ssh_key_data['SSHKEYID']

    def get_available_os_list(self):
        os_list = self.isp.os.list()

        os_obj_list = [
            vps_schema.VpsSpecOsSchema(
                os_code=os_data['OSID'],
                name=os_data['name'],
            ).dict()
            for os_data in os_list.values()
        ]
        return os_obj_list

    def get_available_plans_list(self):
        plan_query_params = {'type': 'vc2'}
        plans_list = self.isp.plans.list(plan_query_params)

        plan_obj_list = [
            vps_schema.VpsSpecPlanSchema(
                plan_code=plan_data['VPSPLANID'],
                name=plan_data['name'],
                vcpu=plan_data['vcpu_count'],
                ram=plan_data['ram'],
                disk=plan_data['disk'],
                bandwidth=plan_data['bandwidth'],
                price_monthly=plan_data['price_per_month'],
                region_codes=plan_data['available_locations'],
            ).dict()
            for plan_data in plans_list.values()
        ]
        return plan_obj_list

    def get_available_regions_list(self):
        region_query_params = {
            'availability': 'yes'
        }
        regions_list = self.isp.regions.list(region_query_params)

        region_obj_list = [
            vps_schema.VpsSpecRegionSchema(
                region_code=region_data['DCID'],
                name=f"{region_data['name']}({region_data['country']}, {region_data['continent']})",
                features=[
                    region_metric_key
                    for region_metric_key, region_metric_value in region_data.items()
                    if isinstance(region_metric_value, bool)
                ],
            ).dict()
            for region_data in regions_list.values()
        ]

        return region_obj_list

    def get_ssh_key_list(self, vps_isp_id: int):
        ssh_key_list = self.isp.sshkey.list()

        ssh_key_obj_list = [
            dict(
                ssh_key_id=key,
                date_created=ssh_key_data['date_created'],
                name=ssh_key_data['name'],
                public_key=ssh_key_data['ssh_key'],
                isp_id=vps_isp_id
            )
            for key, ssh_key_data in ssh_key_list.items()
        ]
        return ssh_key_obj_list

    def destroy_ssh_key(self, ssh_key_id):
        return self.isp.sshkey.destroy(ssh_key_id)

    def create_server(self, vps_profile: dict, public_key: str = None, *args, **kwargs) -> dict:
        tf = Terraform()
        config = tf.gen_vultr_config(vps_profile, self.api_token, public_key)
        state_data = tf.run_terraform_apply(config)
        return state_data

    def start_server(self, server_id, *args, **kwargs) -> bool:
        return self.isp.server.start(server_id)

    def reboot_server(self, server_id, *args, **kwargs) -> bool:
        return self.isp.server.reboot(server_id)

    def shutdown_server(self, server_id, *args, **kwargs) -> bool:
        return self.isp.server.halt(server_id)

    def reinstall_server(self, server_id, *args, **kwargs) -> bool:
        reinstall_params = {
            'hostname': kwargs['hostname']
        } if kwargs else None
        return self.isp.server.reinstall(server_id, reinstall_params)

    def destroy_server(self, server_id, *args, **kwargs) -> bool:
        destroy_result = True
        try:
            self.isp.server.destroy(subid=server_id)
        except VultrError as vultr_error:
            logging.info(vultr_error)
            destroy_result = False
        return destroy_result

    @property
    def api_url(self):
        return self.isp.api_endpoint


class DigitalOceanIsp(BaseVpsIsp):
    def get_isp_obj(self, **kwargs: dict):
        return digitalocean.Manager(token=self.api_token)

    def is_valid_account(self):
        valid = True
        try:
            self.isp.get_account()
        except:
            valid = False
        finally:
            return valid

    def create_ssh_key(self, name: str, public_key_content: str) -> str:
        ssh_key_data = {
            'name': name,
            'public_key': public_key_content
        }
        ssh_key = digitalocean.SSHKey(
            token=self.api_token,
            **ssh_key_data
        )
        ssh_key.create()
        return ssh_key.id

    def get_available_os_list(self):
        os_obj_list = self.isp.get_images(type='distribution')
        os_dict_list = [
            vps_schema.VpsSpecOsSchema(
                os_code=os.id,
                name=f"{os.distribution} {os.name}",
                region_codes=os.regions
            ).dict()
            for os in os_obj_list
        ]

        return os_dict_list

    def get_available_plans_list(self):
        plan_obj_list = self.isp.get_all_sizes()
        plan_dict_list = [
            vps_schema.VpsSpecPlanSchema(
                name=(
                    f"{plan_obj.memory} MB RAM-{plan_obj.vcpus} CPU"
                    f"-{plan_obj.disk} GB-{plan_obj.transfer} TB-{plan_obj.price_monthly}$"
                ),
                plan_code=plan_obj.slug,
                price_monthly=plan_obj.price_monthly,
                bandwidth=plan_obj.transfer,
                region_codes=plan_obj.regions,
                vcpu=plan_obj.vcpus,
                ram=plan_obj.memory,
                disk=plan_obj.disk
            ).dict()
            for plan_obj in plan_obj_list
        ]

        return plan_dict_list

    def get_available_regions_list(self):
        region_obj_list = self.isp.get_all_regions()
        region_dict_list = [
            vps_schema.VpsSpecRegionSchema(
                name=region.name,
                region_code=region.slug,
                plan_codes=region.sizes,
                features=region.features,
            ).dict()
            for region in region_obj_list
        ]

        return region_dict_list

    def get_ssh_key_list(self, vps_isp_id: int):
        ssh_key_list = self.isp.get_all_sshkeys()

        ssh_key_obj_list = [
            dict(
                ssh_key_id=ssh_key.id,
                public_key=ssh_key.public_key,
                name=ssh_key.name,
                fingerprint=ssh_key.fingerprint,
                isp_id=vps_isp_id
            )
            for ssh_key in ssh_key_list
        ]
        return ssh_key_obj_list

    def destroy_ssh_key(self, ssh_key_id):
        return self.isp.get_ssh_key(ssh_key_id).destroy()

    def create_server(self, vps_profile: dict, public_key: str = None, *args, **kwargs) -> dict:
        tf = Terraform()
        if public_key:
            try:
                public_key_fingerprint = gen_ssh_key_fingerprint(public_key)
                public_key_exists = digitalocean.SSHKey.get_object(
                    api_token=self.api_token, ssh_key_id=public_key_fingerprint
                )
            except digitalocean.baseapi.NotFoundError:
                pass
            else:
                if vps_profile['ssh_keys']:
                    vps_profile['ssh_keys'].append(public_key_exists.id)
                else:
                    vps_profile['ssh_keys'] = [public_key_exists.id]
                public_key = None

        config = tf.gen_digital_ocean_config(vps_profile, self.api_token, public_key)
        state_data = tf.run_terraform_apply(config)
        return state_data

    def start_server(self, server_id, *args, **kwargs) -> bool:
        droplet = digitalocean.Droplet(token=self.api_token, id=server_id)
        return droplet.power_on()

    def reboot_server(self, server_id, *args, **kwargs) -> bool:
        droplet = digitalocean.Droplet(token=self.api_token, id=server_id)
        return droplet.reboot()

    def shutdown_server(self, server_id, *args, **kwargs) -> bool:
        droplet = digitalocean.Droplet(token=self.api_token, id=server_id)
        return droplet.power_off()

    def reinstall_server(self, server_id, *args, **kwargs) -> bool:
        droplet = digitalocean.Droplet(token=self.api_token, id=server_id)
        droplet.load()
        return droplet.rebuild()

    def destroy_server(self, server_id, *args, **kwargs) -> bool:
        droplet = digitalocean.Droplet(token=self.api_token, id=server_id)
        destroy_result = True
        try:
            droplet.destroy()
        except digitalocean.baseapi.NotFoundError as droplet_error:
            logging.info(droplet_error)
            destroy_result = False

        return destroy_result

    @property
    def api_url(self):
        return self.isp.end_point
