from celery import Celery

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'services.tasks.settings')
django.setup()

app = Celery('MCMI', task_cls='plugins.task.base:CeleryTask')
app.set_default()
app.config_from_object('django.conf:settings', namespace = 'CELERY')
app.autodiscover_tasks(force = True)
