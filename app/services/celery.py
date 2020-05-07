from celery import Celery

import os


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.core")

app = Celery('MCMI', task_cls='systems.celery.task:CommandTask')
app.config_from_object('django.conf:settings', namespace = 'CELERY')
app.set_default()

if os.environ.get('MCMI_BOOTSTRAP_DJANGO', None):
    import django
    django.setup()
    app.autodiscover_tasks(force = True)
