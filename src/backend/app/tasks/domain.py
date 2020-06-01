from collections import OrderedDict
from io import BytesIO
from tempfile import TemporaryDirectory
from typing import List

from celery import group
from celery.result import allow_join_result
from sqlalchemy.orm import Session

from app.core import config
from app.crud.crud_config import crud_isp
from app.crud.crud_config import crud_ssh_config
from app.crud.crud_domain import crud_domain
from app.crud.crud_domain import crud_domain_dns_record
from app.crud.crud_domain import crud_domain_grow
from app.crud.crud_domain import crud_domain_health
from app.crud.crud_domain import crud_domain_task
from app.db.session import session_manager
from app.libs.domain_verify import review_domain
from app.models.domain import Domain
from app.models.domain import DomainDnsRecord
from app.schemas.domain import DomainCreate
from app.tasks.base import BaseTask
from app.tasks.module import BaseDeployTask
from utils.redis import RedisPool
from app.core.config import PROJECT_NAME
from utils.template import TemplateRender


class ReloadDomainDnsRecordTask(BaseTask):
    name = 'reload_domain_dns_record'

    def run(self, *args, **kwargs):
        with session_manager() as db_session:
            domain_list = crud_domain.get_domain_list(db_session)
            load_domain_extra_data_task = group([
                LoadDomainExtraDataTask().s(domain.id)
                for domain in domain_list
            ])
            load_result = load_domain_extra_data_task.delay()
            with allow_join_result():
                load_result.join()

            return self.set_result()


class LoadDomainExtraDataTask(BaseTask):
    name = 'load_domain_extra_data'

    def run(self, domain_id):
        with session_manager() as db_session:
            domain = crud_domain.get(db_session=db_session, id=domain_id)
            if domain:
                self.load_domain_dns_record(db_session, domain)
                self.load_domain_dns_server(db_session, domain)
        return self.set_result()

    def load_domain_dns_server(self, db_session: Session, domain: Domain) -> None:
        try:
            name_servers = domain.isp_instance.get_domain_info(domain.domain).name_servers
        except Exception as e:
            self.log_exception(e)
        else:
            domain.name_server = ','.join(name_servers)
            db_session.commit()

    def load_domain_dns_record(self, db_session: Session, domain: Domain) -> None:
        try:
            dns_record_list = domain.isp_instance.list_dns_records(domain.domain)
        except Exception as e:
            self.log_exception(e)
        else:
            dns_record_obj_list = [
                DomainDnsRecord(
                    domain_id=domain.id,
                    record_id=dns_record['record_id'],
                    type=dns_record['type'],
                    host=dns_record['host'],
                    value=dns_record['value'],
                    ttl=dns_record['ttl'],
                    distance=dns_record['distance']
                )
                for dns_record in dns_record_list
            ]
            crud_domain_dns_record.filter_by(db_session=db_session, domain_id=domain.id).delete()
            db_session.bulk_save_objects(dns_record_obj_list)


class DetectDomainPurchasableTask(BaseTask):
    name = 'detect_domain_purchasable'

    @classmethod
    def format_domain(cls, domain_str: str) -> str:
        domain_extension_list = [
            ".com", ".net", ".org", ".club", ".us", ".life",
            ".info", ".xyz", ".site", ".tech", ".monster",
            ".world"
        ]

        if "." not in domain_str:
            domain = ','.join([
                f"{domain_str}{domain_extension}"
                for domain_extension in domain_extension_list
            ])
        else:
            domain = domain_str

        return domain.strip()

    @classmethod
    def extract_domain_data(cls, raw_domain_response: dict) -> List:
        raw_domain_data = raw_domain_response.get('domain')
        domain_list = []

        if raw_domain_data:
            # only accept list or dict or str, ignore other cases
            if isinstance(raw_domain_data, list):
                for domain_data in raw_domain_data:
                    if isinstance(domain_data, OrderedDict):
                        domain_list.append({
                            'price': domain_data.get('@price'),
                            'text': domain_data.get('#text')
                        })
                    elif isinstance(domain_data, str):
                        domain_list.append({
                            'text': domain_data
                        })
            elif isinstance(raw_domain_data, OrderedDict):
                domain_list.append({
                    'price': raw_domain_data.get('@price'),
                    'text': raw_domain_data.get('#text')
                })
            elif isinstance(raw_domain_data, str):
                domain_list.append({
                    'text': raw_domain_data
                })

        return domain_list

    def run(self, isp_id: int, domain: str):
        with session_manager() as db_session:
            isp = crud_isp.get(db_session=db_session, id=isp_id)
            isp_instance = isp.isp_instance
        if not isp:
            result = {
                'status': 'pass',
                'msg': f"empty isp via isp_id: {isp_id}"
            }
            return self.set_result(result)

        formatted_domain = self.format_domain(domain)
        domain_detect_result = isp_instance.check_domain_raw(formatted_domain)
        domain_detect_replay_data = domain_detect_result.get('reply', {})

        available_domain_data = domain_detect_replay_data.get("available", {})
        unavailable_domain_data = domain_detect_replay_data.get("unavailable", {})
        domain_list = []

        for available_domain_data in self.extract_domain_data(available_domain_data):
            domain_list.append(dict(purchasable=True, **available_domain_data))
        for unavailable_domain_data in self.extract_domain_data(unavailable_domain_data):
            domain_list.append(dict(purchasable=False, **unavailable_domain_data))

        return domain_list


class PurchaseDomainTask(BaseTask):
    name = 'purchase_domain'

    def run(self, isp_id: int, domain: str, **kwargs: dict):
        with session_manager() as db_session:
            isp = crud_isp.get(db_session=db_session, id=isp_id)
            try:
                register_success = isp.isp_instance.register_domain(domain)
            except Exception as e:
                self.log_exception(e)
                register_success = False
            if register_success:
                domain_profile = DomainCreate(
                    isp_id=isp_id,
                    domain=domain
                )
                crud_domain.create(db_session=db_session, obj_in=domain_profile, serializer=None)
        return register_success


class VerifyDomainTask(BaseTask):
    name = 'verify_domain'

    def run(self, domain: str, vt_token: str = None, **kwargs: dict):
        if not vt_token:
            vt_token = config.VT_API_TOKEN
        return review_domain(domain, vt_token)


class MonitorDomainLoaderTask(BaseTask):
    name = 'monitor_domain_loader'

    def run(self, *args, **kwargs):
        redis_pool = RedisPool()
        with session_manager() as db_session:
            active_task_obj_list = crud_domain_task.get_active_task(db_session=db_session).all()

            for active_task_obj in active_task_obj_list:
                active_task_data = {
                    'id': active_task_obj.id,
                    'interval': active_task_obj.interval,
                    'domain_id': active_task_obj.domain_id,
                    'domain_name': active_task_obj.domain_name
                }
                monitor_task_running_key = redis_pool.gen_task_status_key(
                    status=redis_pool.TASK_RUNNING_STATUS,
                    sequence=active_task_data['id']
                )
                monitor_already_scheduled = redis_pool.exists(monitor_task_running_key)
                if not monitor_already_scheduled:
                    redis_pool.set_data_cache(monitor_task_running_key, 1, ex=active_task_data['interval'])
                    MonitorDomainRunnerTask().delay(active_task_data)


class MonitorDomainRunnerTask(BaseTask):
    name = 'monitor_domain_runner'

    def run(self, task_data: dict, *args, **kwargs):
        with session_manager() as db_session:
            domain_dns_obj_list = crud_domain_dns_record.filter_by(
                db_session=db_session, domain_id=task_data['domain_id']
            )
            for domain_dns_obj in domain_dns_obj_list:
                domain_dns_type = domain_dns_obj.type
                if domain_dns_type.lower() in ['a', 'cname']:
                    domain_health_data = self.fetch_domain_health_record(
                        domain_name=task_data['domain_name']
                    )
                    domain_health_obj = dict(
                        domain_id=task_data['domain_id'],
                        task_id=task_data['id'],
                        host=domain_dns_obj.host,
                        **domain_health_data
                    )
                    crud_domain_health.create(db_session=db_session, obj_in=domain_health_obj, serializer=None)

    def fetch_domain_health_record(self, domain_name: str, vt_token: str = config.VT_API_TOKEN):
        empty_domain_tag_value = "未分类"
        empty_review_value = '无'

        review_domain_result = review_domain(domain_name, vt_token)

        domain_health_data = {
            'talos': review_domain_result.get('talos', empty_domain_tag_value),
            'xforce': review_domain_result.get('xforce', empty_domain_tag_value),
            'opendns': review_domain_result.get('opendns', empty_domain_tag_value),
            'bluecoat': review_domain_result.get('bluecoat', empty_domain_tag_value),
            'mxtoolbox': review_domain_result.get('mxtoolbox', empty_domain_tag_value),
            'trendmicro': review_domain_result.get('trendmicro', empty_domain_tag_value),
            'fortiguard': review_domain_result.get('fortiguard', empty_domain_tag_value),
            'health': review_domain_result.get('health'),
            'explanation': review_domain_result.get('explanation', empty_review_value),
            'health_dns': review_domain_result.get('health_dns'),
        }

        for key in domain_health_data:
            if isinstance(domain_health_data[key], list):
                domain_health_data[key] = ','.join(domain_health_data[key])

        return domain_health_data


class GrowDomainDeployTask(BaseDeployTask):
    name = 'grow_domain'

    def run(self, grow_domain_id: int):
        with session_manager() as db_session:
            grow_domain_obj = crud_domain_grow.get(db_session=db_session, id=grow_domain_id)
            if not grow_domain_obj:
                return

            ip_address = grow_domain_obj.vps.ip
            tmp_dir = TemporaryDirectory()
            ssh_obj = crud_ssh_config.get_config(db_session)
            site_work_dir = f"/opt/{PROJECT_NAME}/site"
            site_data_dir = f"/opt/{PROJECT_NAME}/data"

            # 1. install nginx
            ssh_conn = self.gen_ssh_conn(
                addr=f"root@{ip_address}",
                tmp_dir=tmp_dir.name,
                private_key=ssh_obj.private_key
            )
            install_nginx_command = (
                "command -v yum && yum install -y epel-release && yum install -y nginx unzip;"
                "command -v apt-get && apt-get update -y && apt-get install -y nginx unzip;"
                f"mkdir -p {site_work_dir} {site_data_dir}"
            )

            self.exec_remote_cmd(conn=ssh_conn, command=install_nginx_command)

            # 2. upload template file
            site_template_file_name = grow_domain_obj.template.zip_file_name
            site_template_content = BytesIO(grow_domain_obj.template.zip_file_content).read()

            site_template_tmp_file = self.gen_tmp_file(
                content=site_template_content,
                dir_path=tmp_dir.name
            )
            self.upload_remote_file(
                conn=ssh_conn,
                source_file=site_template_tmp_file.name,
                remote_file=f"{site_data_dir}/{site_template_file_name}"
            )

            # 3. update nginx conf and configure nginx
            self.exec_remote_cmd(
                conn=ssh_conn,
                command=(
                    f"rm -rf {site_work_dir} &&"
                    f"unzip -o -d {site_work_dir} {site_data_dir}/{site_template_file_name};"
                )
            )
            nginx_config_content = TemplateRender().render_nginx_conf(
                nginx_site_work_dir=site_work_dir
            )
            nginx_config_tmp_file = self.gen_tmp_file(
                content=nginx_config_content,
                dir_path=tmp_dir.name
            )
            nginx_conf_deploy_path = f"{site_data_dir}/{TemplateRender.NGINX_TEMPLATE_CONF}"
            self.upload_remote_file(
                conn=ssh_conn,
                source_file=nginx_config_tmp_file.name,
                remote_file=nginx_conf_deploy_path
            )
            self.exec_remote_cmd(
                conn=ssh_conn,
                command=(
                    "ps -aux | grep 'nginx:' | awk '{print $2}'| xargs kill"
                ),
                warn=True
            )
            self.exec_remote_cmd(
                conn=ssh_conn,
                command=(
                    f"nginx -c {nginx_conf_deploy_path}"
                )
            )

            # 4. set dns record
            grow_domain_obj.isp.isp_instance.set_dns_a_record(
                grow_domain_obj.domain_name, ip_address
            )
            return


class GrowDomainDestroyTask(BaseDeployTask):
    name = 'destroy_grow_domain'

    def run(self, grow_domain_id: int):
        with session_manager() as db_session:
            grow_domain_obj = crud_domain_grow.get(db_session=db_session, id=grow_domain_id)
            if not grow_domain_obj:
                return

            ip_address = grow_domain_obj.vps.ip
            if not ip_address:
                return

            tmp_dir = TemporaryDirectory()
            ssh_obj = crud_ssh_config.get_config(db_session)

            ssh_conn = self.gen_ssh_conn(
                addr=f"root@{ip_address}",
                tmp_dir=tmp_dir.name,
                private_key=ssh_obj.private_key
            )
            self.exec_remote_cmd(
                conn=ssh_conn,
                command=(
                    "ps -aux | grep 'nginx:' | awk '{print $2}'| xargs kill"
                ),
                warn=True
            )
            return self.set_result()
