import json

import redis
from sqlalchemy.orm import Session

from core.config import CELERY_TASK_EXPIRE
from core.config import PROJECT_NAME
from core.config import REDIS
from crud.crud_config import crud_isp
from crud.crud_vps import crud_vps


class RedisPool:
    _pool_instance = None
    TASK_SCHEDULED_STATUS = 'scheduled'
    TASK_QUEUED_STATUS = 'queued'
    TASK_RUNNING_STATUS = 'running'

    VPS_SPEC_DATA_KEY_PATTERN = 'vps_spec_{name}'
    VPS_SPEC_CACHE_EXPIRE_TIME = 7 * 24 * 60 * 60

    def __new__(cls, *args, **kwargs):
        redis_host = REDIS.get('host', 'localhost')
        redis_port = REDIS.get('port', 6379)
        redis_db = REDIS.get('db', 0)
        redis_password = REDIS.get('password', None)

        if cls._pool_instance is None:
            cls._pool_instance = redis.ConnectionPool(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                *args, **kwargs
            )
        return super().__new__(cls, *args, **kwargs)

    def __init__(self):
        self.conn = redis.Redis(connection_pool=self._pool_instance)

    def __getattr__(self, name):
        """
        the __getattr__() method is actually a fallback method
        that only gets called when an attribute is not found
        """
        return getattr(self.conn, name)

    @classmethod
    def gen_task_status_key(cls, key_prefix: str = PROJECT_NAME, *, status: str, sequence: int):
        return f"{key_prefix}_{status}_{sequence}"

    def set_data_cache(self, name, value, ex=None, px=None, nx=False, xx=False):
        cache_result = self.conn.set(name, value, ex, px, nx, xx)
        return cache_result

    def set_task_status_data(self, status: str, sequence: int, task_data: str, expire: int = CELERY_TASK_EXPIRE):
        task_status_key = self.gen_task_status_key(status=status, sequence=sequence)
        self.set_data_cache(name=task_status_key, ex=expire, value=task_data)

    def get_matched_key_list(self, pattern: str):
        key_list = [
            key
            for key in self.conn.scan_iter(pattern)
        ]
        return key_list

    def get_vps_spec_data(self, db_session: Session, isp_id: int, reload: bool = False) -> dict:
        vps_spec_data = {}
        vps_isp_obj = crud_isp.get(db_session=db_session, id=isp_id)

        if vps_isp_obj:
            vps_spec_data_key = self.VPS_SPEC_DATA_KEY_PATTERN.format(name=vps_isp_obj.provider_name)
            if reload:
                vps_spec_raw_data = None
            else:
                vps_spec_raw_data = self.conn.get(vps_spec_data_key)

            if vps_spec_raw_data:
                vps_spec_data = json.loads(vps_spec_raw_data)
            else:
                vps_spec_data = crud_vps.get_specs(db_session=db_session, isp_id=isp_id)
                self.set_data_cache(
                    name=vps_spec_data_key,
                    value=json.dumps(vps_spec_data),
                    ex=self.VPS_SPEC_CACHE_EXPIRE_TIME
                )

        return vps_spec_data

    def get_vps_spec_value(self, db_session: Session, isp_id: int, os_code: str, plan_code: str, region_code: str):
        vps_spec_data = self.get_vps_spec_data(db_session, isp_id)
        spec_data = {
            'os': os_code,
            'plan': plan_code,
            'region': region_code
        }
        for spec_key in spec_data:
            for spec_detail in vps_spec_data.get(spec_key, []):
                spec_code = f"{spec_key}_code"
                if spec_data[spec_key] == spec_detail.get(spec_code):
                    spec_data[spec_key] = spec_detail.get('name')
                    break

        return spec_data
