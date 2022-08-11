"""
Application settings definition

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""
from celery.schedules import crontab

from .core import *
from .config import Config

import threading
import importlib


#-------------------------------------------------------------------------------
# Core settings

STARTUP_SERVICES = Config.list('ZIMAGI_STARTUP_SERVICES', [
    'scheduler',
    'command-api',
    'data-api'
])

MANAGER = Manager()

#
# Applications and libraries
#
INSTALLED_APPS = MANAGER.index.get_installed_apps() + [
    'django.contrib.contenttypes',
    'rest_framework',
    'django_filters',
    'corsheaders',
    'settings.app.AppInit'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'systems.cache.middleware.UpdateCacheMiddleware'
] + MANAGER.index.get_installed_middleware() + [
    'systems.cache.middleware.FetchCacheMiddleware'
]

#
# Database configurations
#
DB_PACKAGE_ALL_NAME = Config.string('ZIMAGI_DB_PACKAGE_ALL_NAME', 'all')
DATABASE_ROUTERS = ['systems.db.router.DatabaseRouter']

postgres_service = MANAGER.get_service('pgbouncer')

if postgres_service:
    postgres_host = '127.0.0.1'
    postgres_port = postgres_service['ports']['6432/tcp']
else:
    postgres_host = None
    postgres_port = None

_postgres_host = Config.value('ZIMAGI_POSTGRES_HOST', None)
if _postgres_host:
    postgres_host = _postgres_host

_postgres_port = Config.value('ZIMAGI_POSTGRES_PORT', None)
if _postgres_port:
    postgres_port = _postgres_port

if not postgres_host or not postgres_port:
    raise ConfigurationError("ZIMAGI_POSTGRES_HOST and ZIMAGI_POSTGRES_PORT environment variables required")

postgres_db = Config.string('ZIMAGI_POSTGRES_DB', 'zimagi')
postgres_user = Config.string('ZIMAGI_POSTGRES_USER', 'zimagi')
postgres_password = Config.string('ZIMAGI_POSTGRES_PASSWORD', 'zimagi')
postgres_write_port = Config.value('ZIMAGI_POSTGRES_WRITE_PORT', None)

DATABASES = {
    'default': {
        'ENGINE': 'systems.db.backends.postgresql',
        'NAME': postgres_db,
        'USER': postgres_user,
        'PASSWORD': postgres_password,
        'HOST': postgres_host,
        'PORT': postgres_port,
        'CONN_MAX_AGE': None
    }
}
if postgres_write_port:
    postgres_write_host = Config.value('ZIMAGI_POSTGRES_WRITE_HOST', postgres_host)

    DATABASES['write'] = {
        'ENGINE': 'systems.db.backends.postgresql',
        'NAME': postgres_db,
        'USER': postgres_user,
        'PASSWORD': postgres_password,
        'HOST': postgres_write_host,
        'PORT': postgres_write_port,
        'CONN_MAX_AGE': 1
    }

DISABLE_SERVER_SIDE_CURSORS = True
DB_MAX_CONNECTIONS = Config.integer('ZIMAGI_DB_MAX_CONNECTIONS', 100)
DB_LOCK = threading.Semaphore(DB_MAX_CONNECTIONS)

#
# Redis configurations
#
redis_service = MANAGER.get_service('redis')

if redis_service:
    redis_host = '127.0.0.1'
    redis_port = redis_service['ports']['6379/tcp']
else:
    redis_host = None
    redis_port = None

_redis_host = Config.value('ZIMAGI_REDIS_HOST', None)
if _redis_host:
    redis_host = _redis_host

_redis_port = Config.value('ZIMAGI_REDIS_PORT', None)
if _redis_port:
    redis_port = _redis_port

redis_url = None

if redis_host and redis_port:
    redis_protocol = Config.string('ZIMAGI_REDIS_TYPE', 'redis')
    redis_password = Config.value('ZIMAGI_REDIS_PASSWORD')

    if redis_password:
        redis_url = "{}://:{}@{}:{}".format(
            redis_protocol,
            redis_password,
            redis_host,
            redis_port
        )
    else:
        redis_url = "{}://{}:{}".format(
            redis_protocol,
            redis_host,
            redis_port
        )

#
# Process Management
#
if redis_url:
    REDIS_TASK_URL = "{}/2".format(redis_url)
else:
    REDIS_TASK_URL = None
    QUEUE_COMMANDS = False

#
# Database mutex locking
#
if redis_url:
    REDIS_MUTEX_URL = "{}/3".format(redis_url)
else:
    REDIS_MUTEX_URL = None

MUTEX_TTL_SECONDS = Config.integer('ZIMAGI_MUTEX_TTL_SECONDS', 432000)

#
# Caching configuration
#
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
    },
    'page': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
    }
}

if redis_url and not Config.boolean('ZIMAGI_DISABLE_PAGE_CACHE', False):
    CACHES['page'] = {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "{}/1".format(redis_url),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "IGNORE_EXCEPTIONS": True,
            "PARSER_CLASS": "redis.connection.HiredisParser"
        }
    }

CACHE_MIDDLEWARE_ALIAS = 'page'
CACHE_MIDDLEWARE_KEY_PREFIX = ''
CACHE_MIDDLEWARE_SECONDS = Config.integer('ZIMAGI_PAGE_CACHE_SECONDS', 86400) # 1 Day

CACHE_PARAM = 'refresh'

#
# Email configuration
#
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = Config.value('ZIMAGI_EMAIL_HOST', None)
EMAIL_PORT = Config.integer('ZIMAGI_EMAIL_PORT', 25)
EMAIL_HOST_USER = Config.string('ZIMAGI_EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = Config.string('ZIMAGI_EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = Config.boolean('ZIMAGI_EMAIL_USE_TLS', True)
EMAIL_USE_SSL = Config.boolean('ZIMAGI_EMAIL_USE_SSL', False)
EMAIL_SSL_CERTFILE = Config.value('ZIMAGI_EMAIL_SSL_CERTFILE', None)
EMAIL_SSL_KEYFILE = Config.value('ZIMAGI_EMAIL_SSL_KEYFILE', None)
EMAIL_TIMEOUT = Config.value('ZIMAGI_EMAIL_TIMEOUT', None)
EMAIL_SUBJECT_PREFIX = Config.string('ZIMAGI_EMAIL_SUBJECT_PREFIX', '[Zimagi]>')
EMAIL_USE_LOCALTIME = Config.boolean('ZIMAGI_EMAIL_USE_LOCALTIME', True)

#-------------------------------------------------------------------------------
# Django Addons

#
# API configuration
#
API_INIT = Config.boolean('ZIMAGI_API_INIT', False)
API_EXEC = Config.boolean('ZIMAGI_API_EXEC', False)

WSGI_APPLICATION = 'services.wsgi.application'

ALLOWED_HOSTS = Config.list('ZIMAGI_ALLOWED_HOSTS', ['*'])

REST_PAGE_COUNT = Config.integer('ZIMAGI_REST_PAGE_COUNT', 50)
REST_API_TEST = Config.boolean('ZIMAGI_REST_API_TEST', False)

CORS_ALLOWED_ORIGINS = Config.list('ZIMAGI_CORS_ALLOWED_ORIGINS', [])
CORS_ALLOWED_ORIGIN_REGEXES = Config.list('ZIMAGI_CORS_ALLOWED_ORIGIN_REGEXES', [])
CORS_ALLOW_ALL_ORIGINS = Config.boolean('ZIMAGI_CORS_ALLOW_ALL_ORIGINS', True)

CORS_ALLOW_METHODS = [
    'GET',
    'POST'
]

SECURE_CROSS_ORIGIN_OPENER_POLICY = Config.string('ZIMAGI_SECURE_CROSS_ORIGIN_OPENER_POLICY', 'unsafe-none')
SECURE_REFERRER_POLICY = Config.string('ZIMAGI_SECURE_REFERRER_POLICY', 'no-referrer')

#
# Celery
#
WORKER_PROVIDER = Config.string('ZIMAGI_WORKER_PROVIDER', 'docker')
WORKER_TIMEOUT = Config.integer('ZIMAGI_WORKER_TIMEOUT', 60)
WORKER_CHECK_INTERVAL = Config.integer('ZIMAGI_WORKER_CHECK_INTERVAL', 1)

CELERY_TIMEZONE = TIME_ZONE
CELERY_ACCEPT_CONTENT = ['application/json']

CELERY_BROKER_TRANSPORT_OPTIONS = {
    'max_retries': 3,
    'interval_start': 0,
    'interval_step': 0.2,
    'interval_max': 0.5,
    'master_name': 'zimagi',
    'visibility_timeout': 1800
}
CELERY_BROKER_URL = "{}/0".format(redis_url) if redis_url else None

CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_CREATE_MISSING_QUEUES = True
CELERY_TASK_ACKS_LATE = True
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
        'schedule': crontab(hour='*/2', minute='0')
    },
    'clean_datetime_schedules': {
        'task': 'zimagi.schedule.clean_datetime',
        'schedule': crontab(hour='*/2', minute='0')
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
