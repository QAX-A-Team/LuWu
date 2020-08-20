import os
from datetime import datetime
from datetime import timedelta
from typing import Union

from dotenv import find_dotenv
from dotenv import load_dotenv
from pydantic.json import ENCODERS_BY_TYPE
from pytz import timezone


def getenv_boolean(var_name, default_value=False):
    result = default_value
    env_value = os.getenv(var_name)
    if env_value is not None:
        result = env_value.upper() in ("TRUE", "1")
    return result


# load env
try:
    env_file_path = find_dotenv(raise_error_if_not_found=True)
except IOError:
    env_file_path = find_dotenv(filename='../../conf/backend/env.default')

load_dotenv(env_file_path)

# config settings
API_V1_STR = "/api/v1"
TIMEZONE = timezone('Asia/Shanghai')
SECRET_KEY = os.getenvb(b"SECRET_KEY", os.urandom(32))

ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 8  # 60 minutes * 24 hours * 8 days = 8 days

BACKEND_CORS_ORIGINS = os.getenv("BACKEND_CORS_ORIGINS")
PROJECT_NAME = os.getenv("PROJECT_NAME")

POSTGRES_SERVER = os.getenv("POSTGRES_SERVER")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("POSTGRES_DB")
SQLALCHEMY_DATABASE_URI = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

FIRST_SUPERUSER_EMAIL = os.getenv("FIRST_SUPERUSER_EMAIL")
FIRST_SUPERUSER_USERNAME = os.getenv("FIRST_SUPERUSER_USERNAME")
FIRST_SUPERUSER_PASSWORD = os.getenv("FIRST_SUPERUSER_PASSWORD")

# pagination
PAGINATION_PER_PAGE = 20

# datetime format
DEFAULT_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'


# update format
def local_time_format(o: Union[datetime.date, datetime.time]) -> str:
    return o.astimezone(TIMEZONE).strftime(DEFAULT_DATETIME_FORMAT)


def decode_bytes(bytes_obj: bytes) -> str:
    return bytes_obj.decode('utf-8', 'ignore')


ENCODERS_BY_TYPE.update({
    datetime: local_time_format,
    bytes: decode_bytes,
})

# redis
REDIS = {
    'host': os.getenv("REDIS_HOST", '127.0.0.1'),
    'port': os.getenv("REDIS_PORT", '7003'),
    'password': os.getenv("REDIS_PASSWORD", 'redis_ZAQ!2wsx'),
    'db': os.getenv("REDIS_DB", 0),
}

# celery
CELERY_WORKER_MAX_TASKS_PER_CHILD = 10
CELERY_WORKER_MAX_MEMORY_PER_CHILD = 300000  # 300M
CELERY_TASK_DEFAULT_QUEUE = PROJECT_NAME
CELERY_TASK_DEFAULT_EXCHANGE = PROJECT_NAME
CELERY_TASK_SERIALIZER = 'msgpack'
CELERY_TASK_EXPIRE = 2 * 60 * 60
CELERY_RESULT_SERIALIZER = 'msgpack'
CELERY_ACCEPT_CONTENT = ['msgpack']
CELERY_BROKER_URL = f"redis://:{REDIS['password']}@{REDIS['host']}:{REDIS['port']}/1"
CELERY_RESULT_BACKEND = f"redis://:{REDIS['password']}@{REDIS['host']}:{REDIS['port']}/2"
CELERY_TIMEZONE = 'Asia/Shanghai'
CELERY_RESULT_EXPIRES = 24 * 60 * 60
CELERY_BEAT_SCHEDULE = {
    'cron_task_schedule-every-10-seconds': {
        'task': 'monitor_domain_loader',
        'schedule': timedelta(seconds=10),
        'args': ()
    }
}

# extra config
VT_API_TOKEN = '58f7a81ab4465f4912db1ccb35751162de0b6c2b0d865ce9928a1516dc32e1f4'
TERRAFORM_WORK_DIR = '/terraform'
