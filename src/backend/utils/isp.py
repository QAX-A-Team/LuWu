import json
import logging
from abc import ABC
from abc import abstractmethod
from datetime import datetime
from typing import List

import digitalocean
from aliyunsdkcore.acs_exception.exceptions import ClientException
from aliyunsdkcore.acs_exception.exceptions import ServerException
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import RpcRequest
from aliyunsdkecs.request.v20140526 import AuthorizeSecurityGroupEgressRequest
from aliyunsdkecs.request.v20140526 import AuthorizeSecurityGroupRequest
from aliyunsdkecs.request.v20140526 import CreateSecurityGroupRequest
from aliyunsdkecs.request.v20140526 import DeleteInstanceRequest
from aliyunsdkecs.request.v20140526 import DeleteKeyPairsRequest
from aliyunsdkecs.request.v20140526 import DescribeAvailableResourceRequest
from aliyunsdkecs.request.v20140526 import DescribeImagesRequest
from aliyunsdkecs.request.v20140526 import \
    DescribeImageSupportInstanceTypesRequest
from aliyunsdkecs.request.v20140526 import DescribeInstanceTypesRequest
from aliyunsdkecs.request.v20140526 import DescribeKeyPairsRequest
from aliyunsdkecs.request.v20140526 import DescribeRegionsRequest
from aliyunsdkecs.request.v20140526 import DescribeSecurityGroupsRequest
from aliyunsdkecs.request.v20140526 import ImportKeyPairRequest
from aliyunsdkecs.request.v20140526 import RebootInstanceRequest
from aliyunsdkecs.request.v20140526 import StartInstanceRequest
from aliyunsdkecs.request.v20140526 import StopInstanceRequest
from namesilo.core import NameSilo
from tencentcloud.common import credential as tc_credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import \
    TencentCloudSDKException
from tencentcloud.cvm.v20170312 import cvm_client
from tencentcloud.cvm.v20170312 import models as tc_models
from vultr import Vultr
from vultr import VultrError

from schemas import vps as vps_schema
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
    def register_domain(
        self, domain_name: str, years=1, auto_renew=0, private=0
    ) -> bool:
        pass

    @abstractmethod
    def set_dns_a_record(self, domain_name: str, ip: str) -> bool:
        pass


class NameSiloIsp(BaseDomainIsp):
    def get_isp_obj(self, *args, **kwargs):
        return NameSilo(self.api_token, sandbox=kwargs.get("is_test"))

    def get_domain_info(self, domain_name):
        return self.isp.get_domain_info(domain_name)

    def check_domain(self, domain_name):
        return self.isp.check_domain(domain_name)

    def check_domain_raw(self, domain_name):
        url_extend = (
            f"checkRegisterAvailability?version=1&type=xml&"
            f"key={self.api_token}&domains={domain_name}"
        )
        parsed_content = self.isp._process_data(url_extend)
        return parsed_content.get("namesilo")

    def get_prices(self):
        return self.isp.get_prices()

    def list_dns_records(self, domain_name):
        """
        List dns records for specified domain name
        :param domain_name:
        :return: current domain's dns record
        :rtype: List
        """
        url_extend = "dnsListRecords?version=1&type=xml&key=%s&domain=%s" % (
            self.api_token,
            domain_name,
        )
        parsed_context = self.isp._process_data(url_extend)
        resource_record = parsed_context["namesilo"]["reply"]["resource_record"]

        result = []

        if isinstance(resource_record, list):
            result.extend(resource_record)
        else:
            result.append(resource_record)
        return result

    def register_domain(
        self, domain_name: str, years=1, auto_renew=0, private=1
    ) -> bool:
        return self.isp.register_domain(domain_name, years, auto_renew, private)

    def list_domain_dns_records(self, domain_name: str):
        url_extend = "dnsListRecords?version=1&type=xml&key=%s&domain=%s&rrtype=A" % (
            self.api_token,
            domain_name,
        )
        parsed_context = self.isp._process_data(url_extend)
        return parsed_context

    def set_dns_a_record(self, domain_name: str, ip: str) -> bool:
        url_extend = (
            "dnsAddRecord?version=1&type=xml&key=%s&domain=%s&rrtype=A&rrvalue=%s"
            % (self.api_token, domain_name, ip)
        )
        parsed_context = self.isp._process_data(url_extend)
        detail = parsed_context["namesilo"]["reply"].get("detail")
        return detail == "success"

    @property
    def api_url(self):
        return self.isp._base_url


class BaseVpsIsp(BaseIsp):
    _DEFAULT_SECURITY_GROUP_NAME = "default_sec_group"

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
    def create_server(
        self, vps_profile: dict, public_key: str = None, *args, **kwargs
    ) -> dict:
        tf = Terraform()
        config = tf.gen_ali_config(vps_profile, self.api_token, public_key)
        state_data = tf.run_terraform_apply(config)
        return state_data

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
        except Exception:
            valid = False
        finally:
            return valid

    def create_ssh_key(self, name: str, public_key_content: str) -> str:
        isp_ssh_key_data = self.isp.sshkey.create(name, public_key_content)
        return isp_ssh_key_data["SSHKEYID"]

    def get_available_os_list(self):
        os_list = self.isp.os.list()

        os_obj_list = [
            vps_schema.VpsSpecOsSchema(
                os_code=os_data["OSID"], name=os_data["name"],
            ).dict()
            for os_data in os_list.values()
        ]
        return os_obj_list

    def get_available_plans_list(self):
        plan_query_params = {"type": "vc2"}
        plans_list = self.isp.plans.list(plan_query_params)

        plan_obj_list = [
            vps_schema.VpsSpecPlanSchema(
                plan_code=plan_data["VPSPLANID"],
                name=plan_data["name"],
                vcpu=plan_data["vcpu_count"],
                ram=plan_data["ram"],
                disk=plan_data["disk"],
                bandwidth=plan_data["bandwidth"],
                price_monthly=plan_data["price_per_month"],
                region_codes=plan_data["available_locations"],
            ).dict()
            for plan_data in plans_list.values()
        ]
        return plan_obj_list

    def get_available_regions_list(self):
        region_query_params = {"availability": "yes"}
        regions_list = self.isp.regions.list(region_query_params)

        region_obj_list = [
            vps_schema.VpsSpecRegionSchema(
                region_code=region_data["DCID"],
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
                date_created=ssh_key_data["date_created"],
                name=ssh_key_data["name"],
                public_key=ssh_key_data["ssh_key"],
                isp_id=vps_isp_id,
            )
            for key, ssh_key_data in ssh_key_list.items()
        ]
        return ssh_key_obj_list

    def destroy_ssh_key(self, ssh_key_id):
        return self.isp.sshkey.destroy(ssh_key_id)

    def create_server(
        self, vps_profile: dict, public_key: str = None, *args, **kwargs
    ) -> dict:
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
        reinstall_params = {"hostname": kwargs["hostname"]} if kwargs else None
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
        except Exception:
            valid = False
        finally:
            return valid

    def create_ssh_key(self, name: str, public_key_content: str) -> str:
        ssh_key_data = {"name": name, "public_key": public_key_content}
        ssh_key = digitalocean.SSHKey(token=self.api_token, **ssh_key_data)
        ssh_key.create()
        return ssh_key.id

    def get_available_os_list(self):
        os_obj_list = self.isp.get_images(type="distribution")
        os_dict_list = [
            vps_schema.VpsSpecOsSchema(
                os_code=os.id,
                name=f"{os.distribution} {os.name}",
                region_codes=os.regions,
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
                disk=plan_obj.disk,
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
                isp_id=vps_isp_id,
            )
            for ssh_key in ssh_key_list
        ]
        return ssh_key_obj_list

    def destroy_ssh_key(self, ssh_key_id):
        return self.isp.get_ssh_key(ssh_key_id).destroy()

    def create_server(
        self, vps_profile: dict, public_key: str = None, *args, **kwargs
    ) -> dict:
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
                if vps_profile["ssh_keys"]:
                    vps_profile["ssh_keys"].append(public_key_exists.id)
                else:
                    vps_profile["ssh_keys"] = [public_key_exists.id]
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


class TencentCloudIsp(BaseVpsIsp):
    def get_isp_obj(self, api_id, is_test, *args, **kwargs):
        return tc_credential.Credential(api_id, self.api_token)

    def is_valid_account(self) -> bool:
        try:
            self.get_available_regions_list()
        except TencentCloudSDKException:
            return False
        else:
            return True

    def create_ssh_key(self, name: str, public_key_content: str, region_code: str = None) -> str:
        key_id = None

        if region_code:
            client = cvm_client.CvmClient(self.isp, region_code)
            req = tc_models.ImportKeyPairRequest()
            req_config = json.dumps(dict(ProjectId=0, KeyName=name, PublicKey=public_key_content,))
            req.from_json_string(req_config)
            resp = client.ImportKeyPair(req)
            key_id = resp.KeyId

        return key_id

    def get_available_os_list(self):
        os_map = {}
        os_dict_list = []
        region_list = self.get_available_regions_list()

        for region in region_list:
            region_code = region["region_code"]
            os_list = self.get_available_region_os_list(region_code)
            for os in os_list:
                os_code = os.ImageId
                os_name = os.OsName
                if os_code in os_map:
                    os_map[os_code]["region_codes"].add(region_code)
                else:
                    os_data = dict(
                        os_code=os_code,
                        os_name=os_name,
                        region_codes=set([region_code]),
                    )
                    os_map[os_code] = os_data

        for os_data in os_map.values():
            os_dict_list.append(
                vps_schema.VpsSpecOsSchema(
                    os_code=os_data["os_code"],
                    name=os_data["os_name"],
                    region_codes=list(os_data["region_codes"]),
                ).dict()
            )

        return os_dict_list

    def get_available_region_os_list(self, region_code: str) -> List:
        client = cvm_client.CvmClient(self.isp, region_code)
        req = tc_models.DescribeImagesRequest()
        req.from_json_string('{"Limit":100}')
        resp = client.DescribeImages(req)
        return resp.ImageSet

    def get_available_plans_list(self):
        plan_map = {}
        plan_dict_list = []
        regions_list = self.get_available_regions_list()

        for region in regions_list:
            region_code = region["region_code"]
            plans_list = self.get_available_region_plans_list(region_code)
            for plan in plans_list:
                plan_code = plan.InstanceType
                if plan_code in plan_map:
                    plan_map[plan_code]["region_codes"].add(region_code)
                else:
                    if plan.Price.UnitPrice and plan.Price.ChargeUnit:
                        price_monthly = f"{plan.Price.UnitPrice or plan.Price.OriginalPrice} * {plan.Price.ChargeUnit}"
                    else:
                        price_monthly = plan.Price.OriginalPrice

                    plan_detail_name = (
                        f"{plan.TypeName}({plan.Memory} GB RAM-{plan.Cpu} 核CPU-"
                        f"{plan.CpuType}-{price_monthly} CN¥)"
                    )
                    plan_data = dict(
                        plan_code=plan_code,
                        name=plan_detail_name,
                        vcpu=plan.Cpu,
                        ram=plan.Memory,
                        disk=0,
                        bandwidth=plan.InstanceBandwidth,
                        price_monthly=price_monthly,
                        region_codes=set([region_code]),
                    )
                    plan_map[plan_code] = plan_data

        for plan_data in plan_map.values():
            plan_dict_list.append(
                vps_schema.VpsSpecPlanSchema(
                    plan_code=plan_data["plan_code"],
                    name=plan_data["name"],
                    vcpu=plan_data["vcpu"],
                    ram=plan_data["ram"],
                    disk=plan_data["disk"],
                    bandwidth=plan_data["bandwidth"],
                    price_monthly=plan_data["price_monthly"],
                    region_codes=list(plan_data["region_codes"]),
                ).dict()
            )

        return plan_dict_list

    def get_available_region_plans_list(self, region_code: str) -> List:
        client = cvm_client.CvmClient(self.isp, region_code)
        req = tc_models.DescribeZoneInstanceConfigInfosRequest()
        params = '{\"Filters\":[{\"Name\":\"instance-charge-type\",\"Values\":[\"POSTPAID_BY_HOUR\"]}]}'
        req.from_json_string(params)
        try:
            resp = client.DescribeZoneInstanceConfigInfos(req)
            plan_list = resp.InstanceTypeQuotaSet
        except TencentCloudSDKException as e:
            logging.warning(f"get tencent region plan {region_code} with err: {e}")
            plan_list = []
        return plan_list

    def get_available_regions_list(self):
        client = cvm_client.CvmClient(self.isp, None)
        req = tc_models.DescribeRegionsRequest()
        resp = client.DescribeRegions(req)

        region_dict_list = [
            vps_schema.VpsSpecRegionSchema(
                name=region.RegionName,
                region_code=region.Region,
                plan_codes=[],
                features=None,
            ).dict()
            for region in resp.RegionSet
        ]

        return region_dict_list

    def get_region_zones_list(self, region_code: str) -> List[str]:
        client = cvm_client.CvmClient(self.isp, region_code)
        req = tc_models.DescribeZonesRequest()
        resp = client.DescribeZones(req)

        zones_list = [zone.ZoneId for zone in resp.ZoneSet]
        return zones_list

    def get_ssh_key_list(self, vps_isp_id: int, region_code: str = None) -> List[dict]:
        ssh_key_list = []

        if not region_code:
            regions_list = self.get_available_regions_list()
            region_code = regions_list[0]["region_code"] if regions_list else None

        if region_code:
            client = cvm_client.CvmClient(self.isp, region_code)
            req = tc_models.DescribeKeyPairsRequest()
            req_config = json.dumps(dict(Limit=100,))
            req.from_json_string(req_config)
            resp = client.DescribeKeyPairs(req)

            ssh_key_list = [
                dict(
                    ssh_key_id=key_pair.KeyId,
                    date_created=key_pair.CreatedTime,
                    name=key_pair.KeyName,
                    public_key=key_pair.PublicKey,
                    isp_id=vps_isp_id,
                )
                for key_pair in resp.KeyPairSet
            ]

        return ssh_key_list

    def destroy_ssh_key(self, ssh_key_id):
        client = cvm_client.CvmClient(self.isp)
        req = tc_models.DeleteKeyPairsRequest()
        req_config = json.dumps(dict(KeyIds=[ssh_key_id],))
        req.from_json_string(req_config)
        client.DeleteKeyPairs(req)
        return True

    def create_server(
        self, vps_profile: dict, public_key: str = None, *args, **kwargs
    ) -> dict:
        api_id = self.isp.secretId
        tf = Terraform()
        # attach ssh key
        if public_key:
            ssh_key_name = self.get_or_create_ssh_key_by_public_key(
                public_key, vps_profile["region_code"]
            )
        else:
            ssh_key_name = None
        config = tf.gen_tencent_cloud_config(vps_profile, self.api_token, ssh_key_name, api_id)

        state_data = tf.run_terraform_apply(config)
        return state_data

    def get_or_create_ssh_key_by_public_key(self, public_key: str, region_id: str = None) -> str:
        ssh_key_name = None

        existed_ssh_key = self.get_ssh_key_list(region_id)
        for ssh_key in existed_ssh_key:
            clean_ssh_public_key = ssh_key["public_key"].replace(ssh_key["ssh_key_id"], '').strip()
            public_key_in_tx_format = ' '.join(public_key.split(" ")[:2])
            print(ssh_key, clean_ssh_public_key, public_key_in_tx_format)
            if clean_ssh_public_key == public_key_in_tx_format:
                ssh_key_name = ssh_key["ssh_key_id"]
                break

        if not ssh_key_name:
            now_time = datetime.now()
            unix_timestamp = str(int(now_time.utcnow().timestamp()))
            ssh_key_name = self.create_ssh_key(unix_timestamp, public_key, region_id)
        return ssh_key_name

    def start_server(self, server_id, *args, **kwargs) -> bool:
        regions_list = self.get_available_regions_list()

        for region in regions_list:
            region_code = region["region_code"]

            client = cvm_client.CvmClient(self.isp, region_code)
            req = tc_models.StartInstancesRequest()
            req_config = json.dumps(dict(InstanceIds=[server_id],))
            req.from_json_string(req_config)
            try:
                client.StartInstances(req)
            except Exception as e:
                logging.warning(e)
                started = False
            else:
                started = True
                break

        return started

    def reboot_server(self, server_id, *args, **kwargs) -> bool:
        regions_list = self.get_available_regions_list()

        for region in regions_list:
            region_code = region["region_code"]

            client = cvm_client.CvmClient(self.isp, region_code)
            req = tc_models.RebootInstancesRequest()
            req_config = json.dumps(
                dict(InstanceIds=[server_id], ForceReboot=True,)
            )
            req.from_json_string(req_config)
            try:
                client.RebootInstances(req)
            except Exception as e:
                logging.warning(e)
                rebooted = False
            else:
                rebooted = True
                break
        return rebooted

    def shutdown_server(self, server_id, *args, **kwargs) -> bool:
        regions_list = self.get_available_regions_list()

        for region in regions_list:
            region_code = region["region_code"]

            client = cvm_client.CvmClient(self.isp, region_code)
            req = tc_models.StopInstancesRequest()
            req_config = json.dumps(
                dict(InstanceIds=[server_id], ForceStop=True,)
            )
            req.from_json_string(req_config)
            try:
                client.StopInstances(req)
            except Exception as e:
                logging.warning(e)
                result = False
            else:
                result = True
                break
        return result

    def reinstall_server(self, server_id, *args, **kwargs) -> bool:
        regions_list = self.get_available_regions_list()

        for region in regions_list:
            region_code = region["region_code"]

            client = cvm_client.CvmClient(self.isp, region_code)
            req = tc_models.ResetInstanceRequest()
            req_config = json.dumps(
                dict(
                    InstanceIds=[server_id],
                    LoginSettings=dict(KeepImageLogin=True),
                    EnhancedService=dict(SecurityService=False, MonitorService=False),
                )
            )
            req.from_json_string(req_config)

            try:
                client.ResetInstance(req)
            except Exception as e:
                logging.warning(e)
                result = False
            else:
                result = True
                break
        return result

    def destroy_server(self, server_id, *args, **kwargs) -> bool:
        regions_list = self.get_available_regions_list()

        for region in regions_list:
            region_code = region["region_code"]

            client = cvm_client.CvmClient(self.isp, region_code)
            req = tc_models.TerminateInstancesRequest()
            req_config = json.dumps(dict(InstanceIds=[server_id],))
            req.from_json_string(req_config)

            try:
                client.TerminateInstances(req)
            except Exception as e:
                logging.warning(e)
                result = False
            else:
                result = True
                break
        return result

    @property
    def api_url(self):
        client = cvm_client.CvmClient(self.isp, None)
        return client._endpoint


class AliyunIsp(BaseVpsIsp):
    _ECS_ENDPORINT = "ecs.aliyuncs.com"

    def get_isp_obj(self, api_id, is_test, *args, **kwargs):
        return AcsClient(api_id, self.api_token)

    def handle_request(self, request: RpcRequest, region_id: str = None) -> dict:
        if region_id:
            self.isp.set_region_id(region_id)
        try:
            response = self.isp.do_action_with_exception(request)
        except (ClientException, ServerException) as e:
            logging.warning(request)
            logging.warning(e)
            json_res = {}
        else:
            json_res = json.loads(response)
        return json_res

    def is_valid_account(self) -> bool:
        request = StartInstanceRequest.StartInstanceRequest()
        request.set_DryRun(True)
        valid = self.handle_request(request)
        if valid:
            return True
        else:
            return False

    def create_ssh_key(self, name: str, public_key_content: str) -> str:
        request = ImportKeyPairRequest.ImportKeyPairRequest()
        request.set_KeyPairName(name)
        request.set_PublicKeyBody(public_key_content)

        response = self.handle_request(request)
        return response.get("KeyPairName")

    def get_available_os_list(self):
        os_map = {}
        os_dict_list = []
        region_list = self.get_available_regions_list()

        for region in region_list:
            region_code = region["region_code"]
            os_list = self.get_available_region_os_list(region_code)

            for os in os_list:
                os_code = os["ImageId"]
                os_name = os["OSName"]
                if os_code in os_map:
                    os_map[os_code]["region_codes"].add(region_code)
                else:
                    os_data = dict(
                        os_code=os_code,
                        os_name=os_name,
                        region_codes=set([region_code]),
                        plan_codes=self.get_support_isntance_plan_type(os_code),
                    )
                    os_map[os_code] = os_data

        for os_data in os_map.values():
            os_dict_list.append(
                vps_schema.VpsSpecOsSchema(
                    os_code=os_data["os_code"],
                    name=os_data["os_name"],
                    region_codes=list(os_data["region_codes"]),
                    plan_codes=os_data["plan_codes"],
                ).dict()
            )

        return os_dict_list

    def get_support_isntance_plan_type(self, image_id: str) -> List:
        request = DescribeImageSupportInstanceTypesRequest.DescribeImageSupportInstanceTypesRequest()
        request.set_ImageId(image_id)
        response = self.handle_request(request)
        plan_list = [
            image_type["InstanceTypeId"]
            for image_type in response['InstanceTypes']['InstanceType']
        ]

        return plan_list

    def get_available_region_os_list(self, region_code: str) -> List:
        request = DescribeImagesRequest.DescribeImagesRequest()
        request.set_PageSize(100)
        request.set_ImageOwnerAlias("system")

        response = self.handle_request(request)
        os_list = response["Images"].get("Image", [])

        return os_list

    def get_available_plans_list(self):
        # TODO:query price when aliyun enable price query support
        request = DescribeInstanceTypesRequest.DescribeInstanceTypesRequest()
        response = self.handle_request(request)

        plan_list = [
            vps_schema.VpsSpecPlanSchema(
                plan_code=plan["InstanceTypeId"],
                name=f"{plan['InstanceTypeFamily']}-{plan['MemorySize']}GB RAM-{plan['CpuCoreCount']} 核CPU",
                vcpu=plan["CpuCoreCount"],
                ram=plan["MemorySize"],
                disk=0,
                bandwidth=0,
                price_monthly=0,
                region_codes=[],
            ).dict()
            for plan in response["InstanceTypes"].get("InstanceType", [])
        ]
        return plan_list

    def get_available_region_plan_list(self, region_code: str) -> List:
        request = DescribeAvailableResourceRequest.DescribeAvailableResourceRequest()
        request.set_DestinationResource("InstanceType")
        response = self.handle_request(request)
        region_plan_list = []
        for plan_data in response["AvailableZones"]["AvailableZone"]:
            for region_zone_plan in plan_data["AvailableResources"][
                "AvailableResource"
            ]:
                region_zone_plan_list = [
                    region_zone_plan_data["Value"]
                    for region_zone_plan_data in region_zone_plan["SupportedResources"][
                        "SupportedResource"
                    ]
                    if region_zone_plan_data["Status"] == "Available"
                ]
                region_plan_list.extend(region_zone_plan_list)
  
        region_plan_list = list(set(region_plan_list))
        return region_plan_list

    def get_available_regions_list(self):
        request = DescribeRegionsRequest.DescribeRegionsRequest()
        response = self.handle_request(request)
        region_list = response["Regions"].get("Region", [])

        region_dict_list = [
            vps_schema.VpsSpecRegionSchema(
                name=region_data["LocalName"],
                region_code=region_data["RegionId"],
                plan_codes=self.get_available_region_plan_list(region_data["RegionId"]),
                features=None,
            ).dict()
            for region_data in region_list
            if self.get_available_region_plan_list(region_data["RegionId"])
        ]

        return region_dict_list

    def get_ssh_key_list(self, vps_isp_id: int) -> List[dict]:
        request = DescribeKeyPairsRequest.DescribeKeyPairsRequest()
        request.set_PageSize(50)
        response = self.handle_request(request)
        ssh_key_list = response["KeyPairs"].get("KeyPair", [])

        ssh_key_list = [
            dict(
                fingerprint=key_pair["KeyPairFingerPrint"],
                date_created=key_pair["CreationTime"],
                name=key_pair["KeyPairName"],
                isp_id=vps_isp_id,
            )
            for key_pair in ssh_key_list
        ]

        return ssh_key_list

    def destroy_ssh_key(self, ssh_key_id) -> bool:
        request = DeleteKeyPairsRequest.DeleteKeyPairsRequest()
        request.set_KeyPairNames([ssh_key_id])

        response = self.handle_request(request)
        return bool(response)

    def create_server(
        self, vps_profile: dict, public_key: str = None, *args, **kwargs
    ) -> dict:
        # one ecs only binds to one ssh key pair
        tf = Terraform()
        ak = self.isp.get_access_key()
        # attach ssh key
        if public_key:
            ssh_key_name = self.get_or_create_ssh_key_by_public_key(
                public_key, vps_profile["region_code"]
            )
        # get security groups
        # security_groups = self.get_or_create_default_security_group(vps_profile["region_code"])

        config = tf.gen_ali_cloud_config(vps_profile, self.api_token, ssh_key_name, ak)
        state_data = tf.run_terraform_apply(config)

        return state_data

    def get_or_create_default_security_group(self, region_code: str) -> str:
        query_request = DescribeSecurityGroupsRequest.DescribeSecurityGroupsRequest()
        query_request.set_SecurityGroupName(self._DEFAULT_SECURITY_GROUP_NAME)
        query_response = self.handle_request(query_request, region_id=region_code)
        query_sec_groups = query_response["SecurityGroups"].get("SecurityGroup", [])

        sec_group_id = None

        if query_sec_groups:
            sec_group_id = query_sec_groups[0]["SecurityGroupId"]
        else:
            create_request = CreateSecurityGroupRequest.CreateSecurityGroupRequest()
            create_request.set_SecurityGroupName(self._DEFAULT_SECURITY_GROUP_NAME)
            create_response = self.handle_request(create_request, region_id=region_code)

            sec_group_id = create_response["SecurityGroupId"]
            ip_protocol = "all"
            port_range = "-1/-1"
            source_cidr_ip = "0.0.0.0/0"
            dest_cidr_ip = "0.0.0.0/0"
            policy = "accept"
            self.set_security_group_inner_rule(
                region_code=region_code,
                sec_group_id=sec_group_id,
                source_cidr_ip=source_cidr_ip,
                ip_protocol=ip_protocol,
                port_range=port_range,
                nic_type="internet",
                policy=policy,
            )
            self.set_security_group_outer_rule(
                region_code=region_code,
                sec_group_id=sec_group_id,
                dest_cidr_ip=dest_cidr_ip,
                ip_protocol=ip_protocol,
                port_range=port_range,
                nic_type="internet",
                policy=policy,
            )

        return sec_group_id

    def set_security_group_inner_rule(self, region_code: str, sec_group_id: str, source_cidr_ip: str, ip_protocol: str, port_range: str, nic_type: str, policy: str):
        request = AuthorizeSecurityGroupRequest.AuthorizeSecurityGroupRequest()
        request.set_SecurityGroupId(sec_group_id)
        request.set_SourceCidrIp(source_cidr_ip)
        request.set_IpProtocol(ip_protocol)
        request.set_PortRange(port_range)
        request.set_NicType(nic_type)
        request.set_Policy(policy)

        self.handle_request(request, region_id=region_code)

    def set_security_group_outer_rule(self, region_code: str, sec_group_id: str, dest_cidr_ip: str, ip_protocol: str, port_range: str, nic_type: str, policy: str):
        request = AuthorizeSecurityGroupEgressRequest.AuthorizeSecurityGroupEgressRequest()
        request.set_SecurityGroupId(sec_group_id)
        request.set_DestCidrIp(dest_cidr_ip)
        request.set_IpProtocol(ip_protocol)
        request.set_PortRange(port_range)
        request.set_NicType(nic_type)
        request.set_Policy(policy)

        self.handle_request(request, region_id=region_code)

    def get_or_create_ssh_key_by_public_key(self, public_key: str, region_id: str = None) -> str:
        public_key_md5 = gen_ssh_key_fingerprint(public_key).replace(":", "")
        request = DescribeKeyPairsRequest.DescribeKeyPairsRequest()
        request.set_KeyPairFingerPrint(public_key_md5)
        response = self.handle_request(request, region_id=region_id)
        ssh_keys = response["KeyPairs"].get("KeyPair", [])

        ssh_key_name = None

        if ssh_keys:
            ssh_key_name = ssh_keys[0]["KeyPairName"]

        if not ssh_key_name:
            now_time = datetime.now()
            unix_timestamp = f"luwu_{int(now_time.utcnow().timestamp())}"
            ssh_key_name = self.create_ssh_key(unix_timestamp, public_key)

        return ssh_key_name

    def start_server(self, server_id, *args, **kwargs) -> bool:
        request = StartInstanceRequest.StartInstanceRequest()
        request.set_InstanceId(server_id)
        response = self.handle_request(request)
        return bool(response)

    def reboot_server(self, server_id, *args, **kwargs) -> bool:
        request = RebootInstanceRequest.RebootInstanceRequest()
        request.set_InstanceId(server_id)
        request.set_ForceStop(True)

        response = self.handle_request(request)
        return bool(response)

    def shutdown_server(self, server_id, *args, **kwargs) -> bool:
        request = StopInstanceRequest.StopInstanceRequest()
        request.set_InstanceId(server_id)
        request.set_ConfirmStop(True)
        response = self.handle_request(request)
        return bool(response)

    def reinstall_server(self, server_id, *args, **kwargs) -> bool:
        # unsupported
        return False

    def destroy_server(self, server_id, *args, **kwargs) -> bool:
        request = DeleteInstanceRequest.DeleteInstanceRequest()
        request.set_InstanceId(server_id)
        request.set_Force(True)
        request.set_TerminateSubscription(True)

        response = self.handle_request(request)
        return bool(response)

    @property
    def api_url(self):
        return self._ECS_ENDPORINT


class AlibabaCloudIsp(AliyunIsp):
    def get_isp_obj(self, api_id, is_test, *args, **kwargs):
        return AcsClient(api_id, self.api_token)
