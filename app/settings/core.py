"""
Application settings definition

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""
from celery.schedules import crontab

from systems.manager import Manager
from .config import Config

import os
import sys
import pathlib
import threading

#-------------------------------------------------------------------------------
# Global settings

#
# Directories
#
APP_DIR = '/usr/local/share/mcmi'
DATA_DIR = '/var/local/mcmi'
LIB_DIR = '/usr/local/lib/mcmi'

#-------------------------------------------------------------------------------
# Core Django settings

#
# Development
#
DEBUG = Config.boolean('MCMI_DEBUG', False)

#
# General configurations
#
APP_NAME = 'mcmi'

SECRET_KEY = Config.string('MCMI_SECRET_KEY', 'XXXXXX20181105')

PARALLEL = Config.boolean('MCMI_PARALLEL', True)
THREAD_COUNT = Config.integer('MCMI_THREAD_COUNT', 5)

CLI_EXEC = Config.boolean('MCMI_CLI_EXEC', False)
NO_MIGRATE = Config.boolean('MCMI_NO_MIGRATE', False)

#
# Time configuration
#
TIME_ZONE = Config.string('MCMI_TIME_ZONE', 'America/New_York')
USE_TZ = True

#
# Language configurations
#
LANGUAGE_CODE = Config.string('MCMI_LOCALE', 'en-us')
USE_I18N = True
USE_L10N = True

#
# Display configurations
#
DISPLAY_WIDTH = Config.integer('MCMI_DISPLAY_WIDTH', 80)
DISPLAY_COLOR = Config.boolean('MCMI_DISPLAY_COLOR', True)
COLOR_SOLARIZED = Config.boolean('MCMI_COLOR_SOLARIZED', True)

COMMAND_COLOR = Config.string('MCMI_COMMAND_COLOR', 'cyan')
HEADER_COLOR = Config.string('MCMI_HEADER_COLOR', 'violet')
KEY_COLOR = Config.string('MCMI_KEY_COLOR', 'cyan')
VALUE_COLOR = Config.string('MCMI_VALUE_COLOR', 'violet')
ENCRYPTED_COLOR = Config.string('MCMI_ENCRYPTED_COLOR', 'yellow')
DYNAMIC_COLOR = Config.string('MCMI_DYNAMIC_COLOR', 'magenta')
RELATION_COLOR = Config.string('MCMI_RELATION_COLOR', 'green')
PREFIX_COLOR = Config.string('MCMI_PREFIX_COLOR', 'magenta')
SUCCESS_COLOR = Config.string('MCMI_SUCCESS_COLOR', 'green')
NOTICE_COLOR = Config.string('MCMI_NOTICE_COLOR', 'cyan')
WARNING_COLOR = Config.string('MCMI_WARNING_COLOR', 'orange')
ERROR_COLOR = Config.string('MCMI_ERROR_COLOR', 'red')
TRACEBACK_COLOR = Config.string('MCMI_TRACEBACK_COLOR', 'yellow')

#
# Runtime configurations
#
RUNTIME_PATH = "{}.env".format(os.path.join(DATA_DIR, Config.string('MCMI_RUNTIME_FILE_NAME', 'mcmi')))

DEFAULT_ENV_NAME = Config.string('MCMI_DEFAULT_ENV_NAME', 'default')
DEFAULT_HOST_NAME = Config.string('MCMI_DEFAULT_HOST_NAME', 'default')
DEFAULT_RUNTIME_REPO = Config.string('MCMI_DEFAULT_RUNTIME_REPO', 'registry.hub.docker.com')
DEFAULT_RUNTIME_IMAGE = Config.string('MCMI_DEFAULT_RUNTIME_IMAGE', 'mcmi/mcmi:latest')

LOCK_BASE_PATH = os.path.join(LIB_DIR, Config.string('MCMI_LOCK_DIR', 'lock'))
pathlib.Path(LOCK_BASE_PATH).mkdir(mode = 0o700, parents = True, exist_ok = True)

MODULE_BASE_PATH = os.path.join(LIB_DIR, Config.string('MCMI_MODULES_DIR', 'modules'))
pathlib.Path(MODULE_BASE_PATH).mkdir(mode = 0o700, parents = True, exist_ok = True)

CORE_MODULE = Config.string('MCMI_CORE_MODULE', 'core')
DEFAULT_MODULES = Config.dict('MCMI_DEFAULT_MODULES', {})

MANAGER = Manager(
    APP_DIR,
    DATA_DIR,
    RUNTIME_PATH,
    DEFAULT_ENV_NAME,
    MODULE_BASE_PATH,
    DEFAULT_MODULES
)

#
# Database configurations
#
BASE_DATA_PATH = os.path.join(DATA_DIR, Config.string('MCMI_DATA_FILE_NAME', 'mcmi'))
DATABASE_PROVIDER = 'sqlite'

DB_MAX_CONNECTIONS = Config.integer('MCMI_DB_MAX_CONNECTIONS', 20)
DB_PACKAGE_ALL_NAME = Config.string('MCMI_DB_PACKAGE_ALL_NAME', 'all')

DATABASES = {
    'default': {
        'ENGINE': 'systems.db.backends.sqlite3',
        'OPTIONS': {
            'timeout': 60 # secs
        }
    }
}

mysql_host = Config.value('MCMI_MYSQL_HOST', None)
mysql_port = Config.value('MCMI_MYSQL_PORT', None)

if mysql_host and mysql_port:
    DATABASES['default'] = {
        'ENGINE': 'systems.db.backends.mysql',
        'NAME': Config.string('MCMI_MYSQL_DB', 'mcmi'),
        'USER': Config.string('MCMI_MYSQL_USER', 'mcmi'),
        'PASSWORD': Config.string('MCMI_MYSQL_PASSWORD', 'mcmi'),
        'HOST': mysql_host,
        'PORT': mysql_port,
        'CONN_MAX_AGE': None
    }
    DATABASE_PROVIDER = 'mysql'
else:
    postgres_service = MANAGER.get_service(None, 'mcmi-postgres')
    if postgres_service:
        network_info = postgres_service['ports']['5432/tcp'][0]
        postgres_host = network_info["HostIp"]
        postgres_port = network_info["HostPort"]
    else:
        postgres_host = Config.value('MCMI_POSTGRES_HOST', None)
        postgres_port = Config.value('MCMI_POSTGRES_PORT', None)

    if postgres_host and postgres_port:
        DATABASES['default'] = {
            'ENGINE': 'systems.db.backends.postgresql',
            'NAME': Config.string('MCMI_POSTGRES_DB', 'mcmi'),
            'USER': Config.string('MCMI_POSTGRES_USER', 'mcmi'),
            'PASSWORD': Config.string('MCMI_POSTGRES_PASSWORD', 'mcmi'),
            'HOST': postgres_host,
            'PORT': postgres_port,
            'CONN_MAX_AGE': None
        }
        DATABASE_PROVIDER = 'postgres'

DB_LOCK = threading.Semaphore(DB_MAX_CONNECTIONS)

#
# Applications and libraries
#
INSTALLED_APPS = MANAGER.installed_apps() + [
    'django.contrib.contenttypes',
    'rest_framework',
    'db_mutex'
]

MIDDLEWARE = MANAGER.installed_middleware() + [
    'django.middleware.common.CommonMiddleware',
    'django.middleware.security.SecurityMiddleware'
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
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

#
# Logging configuration
#
LOG_LEVEL = Config.string('MCMI_LOG_LEVEL', 'warning').upper()
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
# Email configuration
#
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = Config.value('MCMI_EMAIL_HOST', None)
EMAIL_PORT = Config.integer('MCMI_EMAIL_PORT', 25)
EMAIL_HOST_USER = Config.string('MCMI_EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = Config.string('MCMI_EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = Config.boolean('MCMI_EMAIL_USE_TLS', True)
EMAIL_USE_SSL = Config.boolean('MCMI_EMAIL_USE_SSL', False)
EMAIL_SSL_CERTFILE = Config.value('MCMI_EMAIL_SSL_CERTFILE', None)
EMAIL_SSL_KEYFILE = Config.value('MCMI_EMAIL_SSL_KEYFILE', None)
EMAIL_TIMEOUT = Config.value('MCMI_EMAIL_TIMEOUT', None)
EMAIL_SUBJECT_PREFIX = Config.string('MCMI_EMAIL_SUBJECT_PREFIX', '[MCMI]> ')
EMAIL_USE_LOCALTIME = Config.boolean('MCMI_EMAIL_USE_LOCALTIME', True)

#-------------------------------------------------------------------------------
# Django Addons

#
# API configuration
#
API_INIT = Config.boolean('MCMI_API_INIT', False)
API_EXEC = Config.boolean('MCMI_API_EXEC', False)

API_HOST = Config.string('MCMI_API_HOST', '0.0.0.0')
API_PORT = Config.integer('MCMI_API_PORT', 5123)

WSGI_APPLICATION = 'services.api.wsgi.application'
ROOT_URLCONF = 'services.api.urls'
ALLOWED_HOSTS = Config.list('MCMI_ALLOWED_HOSTS', ['*'])

REST_FRAMEWORK = {
    'UNAUTHENTICATED_USER': None,
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'systems.api.auth.EncryptedAPITokenAuthentication'
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
        'systems.api.auth.CommandPermission'
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer'
    ]
}

ADMIN_USER = Config.string('MCMI_ADMIN_USER', 'admin')
DEFAULT_ADMIN_TOKEN = Config.string('MCMI_DEFAULT_ADMIN_TOKEN', 'a11223344556677889900z')

#
# Database mutex locking
#
DB_MUTEX_TTL_SECONDS = Config.integer('MCMI_MUTEX_TTL_SECONDS', 300)

#
# Celery
#
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BROKER_URL = None
CELERY_BROKER_TRANSPORT_OPTIONS = {
    'max_retries': 3,
    'interval_start': 0,
    'interval_step': 0.2,
    'interval_max': 0.5,
    'master_name': 'mcmi',
    'visibility_timeout': 1800
}

queue_service = MANAGER.get_service(None, 'mcmi-queue')
if queue_service:
    network_info = queue_service['ports']['6379/tcp'][0]
    redis_host = network_info["HostIp"]
    redis_port = network_info["HostPort"]
else:
    redis_host = Config.value('MCMI_REDIS_HOST', None)
    redis_port = Config.value('MCMI_REDIS_PORT', None)

if redis_host and redis_port:
    CELERY_BROKER_URL = "{}://:{}@{}:{}".format(
        Config.string('MCMI_REDIS_TYPE', 'redis'),
        Config.string('MCMI_REDIS_PASSWORD', 'mcmi'),
        redis_host,
        redis_port
    )

CELERY_BEAT_SCHEDULE = {
    'clean_interval_schedules': {
        'task': 'mcmi.schedule.clean_interval',
        'schedule': crontab(hour='*/2', minute='0')
    },
    'clean_crontab_schedules': {
        'task': 'mcmi.schedule.clean_crontab',
        'schedule': crontab(hour='*/2', minute='0')
    },
    'clean_datetime_schedules': {
        'task': 'mcmi.schedule.clean_datetime',
        'schedule': crontab(hour='*/2', minute='0')
    }
}

#-------------------------------------------------------------------------------
# External module settings

for settings_module in MANAGER.settings_modules():
    for setting in dir(settings_module):
        if setting == setting.upper():
            locals()[setting] = getattr(settings_module, setting)
