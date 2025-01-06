import logging
import os

import django
from celery.signals import before_task_publish, celeryd_init, worker_shutting_down
from kombu import Queue
from systems.celery.app import Celery
from systems.models.overrides import *  # noqa: F401, F403
from utility.data import dump_json
from utility.mutex import Mutex

logger = logging.getLogger(__name__)


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.full")

#
# Celery initialization
#
manager = None
app = Celery("Zimagi", task_cls="systems.celery.task:CommandTask")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.set_default()

django.setup()
app.autodiscover_tasks(force=True)

if os.environ.get("ZIMAGI_SCHEDULER_EXEC", None):
    from django.conf import settings

    if settings.RESTART_SERVICES:
        settings.MANAGER.restart_services()

    Mutex.set("startup_scheduler")

elif os.environ.get("ZIMAGI_WORKER_EXEC", None):
    from systems.celery.worker import start_worker_manager

    manager = start_worker_manager(app)


#
# Celery hooks
#
@celeryd_init.connect
def capture_service_name(sender, instance, **kwargs):
    os.environ["ZIMAGI_CELERY_NAME"] = sender


@before_task_publish.connect
def task_sent_handler(sender, headers=None, body=None, **kwargs):
    from django.conf import settings
    from systems.commands.action import ActionCommand

    active_command = settings.MANAGER.active_command
    worker_command = ActionCommand("worker")
    queue = None

    for entity in kwargs["declare"]:
        if isinstance(entity, Queue):
            queue = entity.name
            break
    if queue and body and body[0] and body[1]:
        logger.info(f"Executing worker {queue} task with: {dump_json(body, indent=2)}")
        try:
            worker = worker_command.get_provider(
                "worker", settings.WORKER_PROVIDER, app, worker_type=queue, command_name=body[0][0], command_options=body[1]
            )
            worker.ensure()

        except Exception as e:
            if active_command:
                active_command.error(f"Worker processor failed to start: {e}", terminate=False)
                active_command.set_status(False)
                active_command.log_status(False)
                active_command.publish_exit()


@worker_shutting_down.connect
def cleanup_worker_manager(*args, **kwargs):
    if manager:
        manager.terminate()
