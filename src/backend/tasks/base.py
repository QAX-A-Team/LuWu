import logging
import traceback
from datetime import datetime
from typing import Union

import celery
import pytz
from celery.utils.time import get_exponential_backoff_interval

from core import config


class BaseTask(celery.Task):
    resultrepr_maxsize = 10240
    expires = config.CELERY_TASK_EXPIRE

    autoretry_for = (Exception,)
    retry_kwargs = {
        'max_retries': 3,
    }
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_time = self.now_time

        if self.autoretry_for and not hasattr(self, '_orig_run'):
            def run(*args, **kwargs):
                try:
                    return self._orig_run(*args, **kwargs)
                except self.autoretry_for as exc:
                    if self.request_stack:
                        if 'countdown' not in self.retry_kwargs:
                            countdown = get_exponential_backoff_interval(
                                factor=self.retry_backoff,
                                retries=self.request.retries,
                                maximum=self.retry_backoff_max,
                                full_jitter=self.retry_jitter,
                            )

                            retry_kwargs = self.retry_kwargs.copy()
                            retry_kwargs.update({'countdown': countdown})
                        else:
                            retry_kwargs = self.retry_kwargs

                        retry_kwargs.update({'exc': exc})
                        raise self.retry(**retry_kwargs)
                    else:
                        logging.warning('no celery task request stack')
                        logging.warning(traceback.format_exc())
                finally:
                    self.start_time = self.now_time
            self._orig_run, self.run = self.run, run

    def run(self, *args, **kwargs):
        """
        Entry point for task
        """
        raise NotImplementedError

    def set_result(self, extra_data_dict: dict = {}) -> dict:
        base_result = {
            'task_name': self.name,
            'start_time': self.start_time.strftime(config.DEFAULT_DATETIME_FORMAT),
            'end_time': self.now_time_str
        }
        base_result.update(extra_data_dict)
        return base_result

    @property
    def now_time(self) -> datetime:
        return self.get_now_time()

    @property
    def now_time_str(self) -> str:
        return self.now_time.strftime(config.DEFAULT_DATETIME_FORMAT)

    @property
    def request_id(self) -> Union[str, None]:
        if self.request_stack:
            request_id = self.request.id
        else:
            request_id = f"miss_req_stack_{self.now_time_str}"
        return request_id

    @classmethod
    def get_now_time(cls, local_tz: str = config.CELERY_TIMEZONE) -> datetime:
        locale_to_use = pytz.timezone(local_tz)
        current_time = locale_to_use.localize(datetime.now())
        return current_time

    def on_retry(self, exc, task_id, args, kwargs, einfo) -> None:
        retry_msg = f"task_name: {self.name}, task_id: {task_id}, args: {args}, kwargs: {kwargs} einfo: {einfo}"
        logging.warning(retry_msg)

    def on_failure(self, exc, task_id, args, kwargs, einfo) -> None:
        pass

    def log_exception(self, exc=traceback.format_exc()) -> None:
        exc_msg = f"task: {self.name}, exc: {exc}"
        logging.warning(exc_msg)
