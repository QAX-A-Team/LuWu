import inspect

from celery import Celery

from core import config
from tasks import config as config_task
from tasks import domain as domain_task
from tasks import module as module_task
from tasks import vps as vps_task
from tasks.base import BaseTask


def auto_load_task(app, task_module_list):
    for task_module in task_module_list:
        for task_member in inspect.getmembers(task_module, inspect.isclass):
            _, task_class = task_member
            is_task = all([
                issubclass(task_class, BaseTask),
                getattr(task_class, 'name', None)
            ])
            if is_task:
                app.tasks.register(task_class)


celery_app = Celery(config.PROJECT_NAME)
celery_app.config_from_object(config, namespace='CELERY')

task_list = [config_task, domain_task, module_task, vps_task]
auto_load_task(celery_app, task_list)
