"""
Application settings definition

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""
from celery.schedules import crontab

from .full import *
from .config import Config

import importlib


#-------------------------------------------------------------------------------
# Core settings

#-------------------------------------------------------------------------------
# Django Addons

#
# Celery
#
CELERY_TIMEZONE = TIME_ZONE
CELERY_ACCEPT_CONTENT = ['application/json']

CELERY_BROKER_TRANSPORT_OPTIONS = {
    'master_name': 'zimagi',
    'visibility_timeout': 1800
}
CELERY_BROKER_URL = "{}/0".format(redis_url) if redis_url else None

CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_CREATE_MISSING_QUEUES = True
CELERY_TASK_ACKS_LATE = False
CELERY_TASK_SERIALIZER = 'json'
CELERY_TASK_ROUTES = {
    'celery.*': 'default',
    'zimagi.schedule.*': 'default',
    'zimagi.notification.*': 'default'
}

CELERY_BEAT_SCHEDULE = {
    'clean_interval_schedules': {
        'task': 'zimagi.schedule.clean_interval',
        'schedule': crontab(hour='*/2', minute='0')
    },
    'clean_crontab_schedules': {
        'task': 'zimagi.schedule.clean_crontab',
        'schedule': crontab(hour='*/2', minute='15')
    },
    'clean_datetime_schedules': {
        'task': 'zimagi.schedule.clean_datetime',
        'schedule': crontab(hour='*/2', minute='30')
    }
}

#-------------------------------------------------------------------------------
# Service specific settings

service_module = importlib.import_module("services.{}.settings".format(APP_SERVICE))
for setting in dir(service_module):
    if setting == setting.upper():
        locals()[setting] = getattr(service_module, setting)

#-------------------------------------------------------------------------------
# External module settings

for settings_module in MANAGER.index.get_settings_modules():
    for setting in dir(settings_module):
        if setting == setting.upper():
            locals()[setting] = getattr(settings_module, setting)

#-------------------------------------------------------------------------------
# Manager initialization

MANAGER.initialize()
