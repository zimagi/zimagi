from systems.celery.app import Celery
from systems.models.overrides import *

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.full")

manager = None
app = Celery('Zimagi',
    task_cls = 'systems.celery.task:CommandTask'
)
app.config_from_object('django.conf:settings', namespace = 'CELERY')
app.set_default()

if os.environ.get('ZIMAGI_BOOTSTRAP_DJANGO', None):
    import django
    django.setup()
    app.autodiscover_tasks(force = True)
