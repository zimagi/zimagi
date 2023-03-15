from celery.signals import celeryd_init, before_task_publish, worker_shutting_down
from kombu import Queue

from systems.celery.app import Celery
from systems.models.overrides import *
from utility.mutex import Mutex

import os
import django
import json
import logging


logger = logging.getLogger(__name__)


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.full")

#
# Celery initialization
#
manager = None
app = Celery('Zimagi',
    task_cls = 'systems.celery.task:CommandTask'
)
app.config_from_object('django.conf:settings', namespace = 'CELERY')
app.set_default()

django.setup()
app.autodiscover_tasks(force = True)

if os.environ.get('ZIMAGI_SCHEDULER_EXEC', None):
    from django.conf import settings
    settings.MANAGER.restart_services()
    Mutex.set('startup_scheduler')

elif os.environ.get('ZIMAGI_WORKER_EXEC', None):
    from systems.celery.worker import start_worker_manager
    manager = start_worker_manager(app)

#
# Celery hooks
#
@celeryd_init.connect
def capture_service_name(sender, instance, **kwargs):
    os.environ['ZIMAGI_CELERY_NAME'] = sender

@before_task_publish.connect
def task_sent_handler(sender, headers = None, body = None, **kwargs):
    from django.conf import settings
    from systems.commands.action import ActionCommand

    command = ActionCommand('worker')
    queue = None

    for entity in kwargs['declare']:
        if isinstance(entity, Queue):
            queue = entity.name
            break
    if queue and body and body[0] and body[1]:
        logger.info("Executing worker {} task with: {}".format(
            queue,
            json.dumps(body, indent = 2)
        ))
        worker = command.get_provider('worker', settings.WORKER_PROVIDER, app,
            worker_type = queue,
            command_name = body[0][0],
            command_options = body[1]
        )
        worker.ensure()

@worker_shutting_down.connect
def cleanup_worker_manager(*args, **kwargs):
    if manager:
        manager.terminate()
