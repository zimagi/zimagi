"""
Application settings definition

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""
from celery.schedules import crontab

from systems.manager import Manager
from .config import Config

import os
import pathlib
import threading
import importlib
import colorful


class ConfigurationError(Exception):
    pass


#-------------------------------------------------------------------------------
# Core settings

#
# Directories
#
APP_DIR = '/usr/local/share/zimagi'
DATA_DIR = '/var/local/zimagi'
LIB_DIR = '/usr/local/lib/zimagi'

HOST_APP_DIR = Config.value('ZIMAGI_HOST_APP_DIR', None)
HOST_DATA_DIR = Config.value('ZIMAGI_HOST_DATA_DIR', None)
HOST_LIB_DIR = Config.value('ZIMAGI_HOST_LIB_DIR', None)

#
# Development
#
DEBUG = Config.boolean('ZIMAGI_DEBUG', False)
DEBUG_COMMAND_PROFILES = Config.boolean('ZIMAGI_DEBUG_COMMAND_PROFILES', False)

INIT_PROFILE = Config.boolean('ZIMAGI_INIT_PROFILE', False)
COMMAND_PROFILE = Config.boolean('ZIMAGI_COMMAND_PROFILE', False)
DISABLE_MODULE_INIT = Config.boolean('ZIMAGI_DISABLE_MODULE_INIT', False)
DISABLE_REMOVE_ERROR_MODULE = Config.boolean('ZIMAGI_DISABLE_REMOVE_ERROR_MODULE', False)

#
# General configurations
#
APP_NAME = Config.string('ZIMAGI_APP_NAME', 'zimagi', default_on_empty = True)
APP_SERVICE = Config.string('ZIMAGI_SERVICE', 'cli', default_on_empty = True)
SECRET_KEY = Config.string('ZIMAGI_SECRET_KEY', 'XXXXXX20181105')

ENCRYPT_COMMAND_API = Config.boolean('ZIMAGI_ENCRYPT_COMMAND_API', True)
ENCRYPT_DATA_API = Config.boolean('ZIMAGI_ENCRYPT_DATA_API', True)
ENCRYPT_DATA = Config.boolean('ZIMAGI_ENCRYPT_DATA', True)

ENCRYPTION_STATE_PROVIDER = Config.string('ZIMAGI_ENCRYPTION_STATE_PROVIDER', 'aes256')
ENCRYPTION_STATE_KEY = Config.string('ZIMAGI_ENCRYPTION_STATE_KEY', '/etc/ssl/certs/zimagi.crt')

PARALLEL = Config.boolean('ZIMAGI_PARALLEL', True)
THREAD_COUNT = Config.integer('ZIMAGI_THREAD_COUNT', 10)
QUEUE_COMMANDS = Config.boolean('ZIMAGI_QUEUE_COMMANDS', True)
FOLLOW_QUEUE_COMMAND = Config.boolean('ZIMAGI_FOLLOW_QUEUE_COMMAND', True)

CLI_EXEC = Config.boolean('ZIMAGI_CLI_EXEC', False)

NO_MIGRATE = Config.boolean('ZIMAGI_NO_MIGRATE', False)
AUTO_MIGRATE_TIMEOUT = Config.integer('ZIMAGI_AUTO_MIGRATE_TIMEOUT', 300)
AUTO_MIGRATE_INTERVAL = Config.integer('ZIMAGI_AUTO_MIGRATE_INTERVAL', 5)

ROLE_PROVIDER = Config.string('ZIMAGI_ROLE_PROVIDER', 'role')

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

#
# Time configuration
#
TIME_ZONE = Config.string('ZIMAGI_TIME_ZONE', 'America/New_York')
USE_TZ = True

DEFAULT_DATE_FORMAT = Config.string('ZIMAGI_DEFAULT_DATE_FORMAT', '%Y-%m-%d')
DEFAULT_TIME_FORMAT = Config.string('ZIMAGI_DEFAULT_TIME_FORMAT', '%H:%M:%S')
DEFAULT_TIME_SPACER_FORMAT = Config.string('ZIMAGI_DEFAULT_TIME_SPACER_FORMAT', ' ')

#
# Language configurations
#
LANGUAGE_CODE = Config.string('ZIMAGI_LOCALE', 'en')
USE_I18N = True
USE_L10N = True

#
# Display configurations
#
DISPLAY_LOCK = threading.Lock()

DISPLAY_WIDTH = Config.integer('ZIMAGI_DISPLAY_WIDTH', 80)
DISPLAY_COLOR = Config.boolean('ZIMAGI_DISPLAY_COLOR', True)
COLOR_SOLARIZED = Config.boolean('ZIMAGI_COLOR_SOLARIZED', True)

COMMAND_COLOR = Config.string('ZIMAGI_COMMAND_COLOR', 'cyan')
HEADER_COLOR = Config.string('ZIMAGI_HEADER_COLOR', 'violet')
KEY_COLOR = Config.string('ZIMAGI_KEY_COLOR', 'cyan')
VALUE_COLOR = Config.string('ZIMAGI_VALUE_COLOR', 'violet')
ENCRYPTED_COLOR = Config.string('ZIMAGI_ENCRYPTED_COLOR', 'yellow')
DYNAMIC_COLOR = Config.string('ZIMAGI_DYNAMIC_COLOR', 'magenta')
RELATION_COLOR = Config.string('ZIMAGI_RELATION_COLOR', 'green')
PREFIX_COLOR = Config.string('ZIMAGI_PREFIX_COLOR', 'magenta')
SUCCESS_COLOR = Config.string('ZIMAGI_SUCCESS_COLOR', 'green')
NOTICE_COLOR = Config.string('ZIMAGI_NOTICE_COLOR', 'cyan')
WARNING_COLOR = Config.string('ZIMAGI_WARNING_COLOR', 'orange')
ERROR_COLOR = Config.string('ZIMAGI_ERROR_COLOR', 'red')
TRACEBACK_COLOR = Config.string('ZIMAGI_TRACEBACK_COLOR', 'yellow')

colorful.use_true_colors()

if COLOR_SOLARIZED:
    colorful.use_style('solarized')

#
# Runtime configurations
#
BASE_DATA_PATH = os.path.join(DATA_DIR, 'zimagi')
RUNTIME_PATH = "{}.yml".format(BASE_DATA_PATH)

DEFAULT_ENV_NAME = Config.string('ZIMAGI_DEFAULT_ENV_NAME', 'default')
DEFAULT_HOST_NAME = Config.string('ZIMAGI_DEFAULT_HOST_NAME', 'default')
DEFAULT_RUNTIME_REPO = Config.string('ZIMAGI_DEFAULT_RUNTIME_REPO', 'registry.hub.docker.com')
DEFAULT_RUNTIME_IMAGE = Config.string('ZIMAGI_DEFAULT_RUNTIME_IMAGE', 'zimagi/zimagi:latest')
RUNTIME_IMAGE = Config.string('ZIMAGI_RUNTIME_IMAGE', DEFAULT_RUNTIME_IMAGE)

MODULE_BASE_PATH = os.path.join(LIB_DIR, 'modules')
pathlib.Path(MODULE_BASE_PATH).mkdir(parents = True, exist_ok = True)

TEMPLATE_BASE_PATH = os.path.join(LIB_DIR, 'templates')
pathlib.Path(TEMPLATE_BASE_PATH).mkdir(parents = True, exist_ok = True)

DATASET_BASE_PATH = os.path.join(LIB_DIR, 'datasets')
pathlib.Path(DATASET_BASE_PATH).mkdir(parents = True, exist_ok = True)

PROFILER_PATH = os.path.join(LIB_DIR, 'profiler')
pathlib.Path(PROFILER_PATH).mkdir(parents = True, exist_ok = True)

CORE_MODULE = Config.string('ZIMAGI_CORE_MODULE', 'core')
DEFAULT_MODULES = Config.list('ZIMAGI_DEFAULT_MODULES', [])

STARTUP_SERVICES = Config.list('ZIMAGI_STARTUP_SERVICES', [
    'scheduler',
    'worker',
    'command-api',
    'data-api'
])

MANAGER = Manager()

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
redis_service = MANAGER.get_service('redis', create = False)

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
# Applications and libraries
#
INSTALLED_APPS = MANAGER.index.get_installed_apps() + [
    'django.contrib.contenttypes',
    'rest_framework',
    'rest_framework_filters',
    'django_filters',
    'db_mutex',
    'settings.app.AppInit'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'systems.cache.middleware.UpdateCacheMiddleware'
] + MANAGER.index.get_installed_middleware() + [
    'systems.cache.middleware.FetchCacheMiddleware'
]

#
# Authentication configuration
#
AUTH_USER_MODEL = 'user.User'

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

#
# Logging configuration
#
LOG_LEVEL = Config.string('ZIMAGI_LOG_LEVEL', 'warning').upper()
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt' : "%d/%b/%Y %H:%M:%S"
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        }
    },
    'loggers': {
        '': {
            'level': LOG_LEVEL,
            'handlers': ['console']
        }
    }
}

#
# System check settings
#
SILENCED_SYSTEM_CHECKS = []

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

ADMIN_USER = Config.string('ZIMAGI_ADMIN_USER', 'admin')
DEFAULT_ADMIN_TOKEN = Config.string('ZIMAGI_DEFAULT_ADMIN_TOKEN', 'a11223344556677889900z')

#
# Database mutex locking
#
DB_MUTEX_TTL_SECONDS = Config.integer('ZIMAGI_MUTEX_TTL_SECONDS', 432000)

#
# Celery
#
CELERY_TIMEZONE = TIME_ZONE
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_SERIALIZER = 'json'
CELERY_BROKER_URL = None
CELERY_BROKER_TRANSPORT_OPTIONS = {
    'max_retries': 3,
    'interval_start': 0,
    'interval_step': 0.2,
    'interval_max': 0.5,
    'master_name': 'zimagi',
    'visibility_timeout': 1800
}

if redis_url:
    CELERY_BROKER_URL = "{}/0".format(redis_url)

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
