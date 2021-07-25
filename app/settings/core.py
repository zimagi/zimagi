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
import importlib
import colorful

#-------------------------------------------------------------------------------
# Global settings

#
# Directories
#
APP_DIR = '/usr/local/share/zimagi'
DATA_DIR = '/var/local/zimagi'
LIB_DIR = '/usr/local/lib/zimagi'

#-------------------------------------------------------------------------------
# Core Django settings

#
# Development
#
DEBUG = Config.boolean('ZIMAGI_DEBUG', False)
INIT_PROFILE = Config.boolean('ZIMAGI_INIT_PROFILE', False)
COMMAND_PROFILE = Config.boolean('ZIMAGI_COMMAND_PROFILE', False)
DISABLE_MODULE_INIT = Config.boolean('ZIMAGI_DISABLE_MODULE_INIT', False)
DISABLE_REMOVE_ERROR_MODULE = Config.boolean('ZIMAGI_DISABLE_REMOVE_ERROR_MODULE', False)

#
# General configurations
#
APP_NAME = 'zimagi'
APP_SERVICE = Config.string('ZIMAGI_SERVICE', 'cli')

SECRET_KEY = Config.string('ZIMAGI_SECRET_KEY', 'XXXXXX20181105')

PARALLEL = Config.boolean('ZIMAGI_PARALLEL', True)
THREAD_COUNT = Config.integer('ZIMAGI_THREAD_COUNT', 5)

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

MODULE_BASE_PATH = os.path.join(LIB_DIR, Config.string('ZIMAGI_MODULES_DIR', 'modules'))
pathlib.Path(MODULE_BASE_PATH).mkdir(mode = 0o700, parents = True, exist_ok = True)

DATASET_BASE_PATH = os.path.join(LIB_DIR, Config.string('ZIMAGI_DATASET_DIR', 'datasets'))
pathlib.Path(DATASET_BASE_PATH).mkdir(mode = 0o700, parents = True, exist_ok = True)

PROFILER_PATH = os.path.join(LIB_DIR, Config.string('ZIMAGI_PROFILER_DIR', 'profiler'))
pathlib.Path(PROFILER_PATH).mkdir(mode = 0o755, parents = True, exist_ok = True)

CORE_MODULE = Config.string('ZIMAGI_CORE_MODULE', 'core')
DEFAULT_MODULES = Config.list('ZIMAGI_DEFAULT_MODULES', [])

MANAGER = Manager()

#
# Database configurations
#
DATABASE_ROUTERS = ['systems.db.router.DatabaseRouter']
DATABASE_PROVIDER = 'sqlite'

DB_MAX_CONNECTIONS = 1
DB_PACKAGE_ALL_NAME = Config.string('ZIMAGI_DB_PACKAGE_ALL_NAME', 'all')

DATABASES = {
    'default': {
        'ENGINE': 'systems.db.backends.sqlite3',
        'OPTIONS': {
            'timeout': 60 # secs
        }
    }
}

mysql_host = Config.value('ZIMAGI_MYSQL_HOST', None)
mysql_port = Config.value('ZIMAGI_MYSQL_PORT', None)

if mysql_host and mysql_port:
    mysql_db = Config.string('ZIMAGI_MYSQL_DB', 'zimagi')
    mysql_user = Config.string('ZIMAGI_MYSQL_USER', 'zimagi')
    mysql_password = Config.string('ZIMAGI_MYSQL_PASSWORD', 'zimagi')
    mysql_write_port = Config.value('ZIMAGI_MYSQL_WRITE_PORT', None)

    DATABASES['default'] = {
        'ENGINE': 'systems.db.backends.mysql',
        'NAME': mysql_db,
        'USER': mysql_user,
        'PASSWORD': mysql_password,
        'HOST': mysql_host,
        'PORT': mysql_port,
        'CONN_MAX_AGE': 120
    }
    if mysql_write_port:
        mysql_write_host = Config.value('ZIMAGI_MYSQL_WRITE_HOST', mysql_host)

        DATABASES['write'] = {
            'ENGINE': 'systems.db.backends.mysql',
            'NAME': mysql_db,
            'USER': mysql_user,
            'PASSWORD': mysql_password,
            'HOST': mysql_write_host,
            'PORT': mysql_write_port,
            'CONN_MAX_AGE': 120
        }
    DATABASE_PROVIDER = 'mysql'
    DB_MAX_CONNECTIONS = Config.integer('ZIMAGI_DB_MAX_CONNECTIONS', 10)
else:
    postgres_service = MANAGER.get_service(None, 'zimagi-postgres')
    postgres_db = Config.string('ZIMAGI_POSTGRES_DB', 'zimagi')
    postgres_user = Config.string('ZIMAGI_POSTGRES_USER', 'zimagi')
    postgres_password = Config.string('ZIMAGI_POSTGRES_PASSWORD', 'zimagi')
    postgres_write_port = Config.value('ZIMAGI_POSTGRES_WRITE_PORT', None)

    if postgres_service:
        network_info = postgres_service['ports']['5432/tcp'][0]
        postgres_host = network_info["HostIp"]
        postgres_port = network_info["HostPort"]
    else:
        postgres_host = Config.value('ZIMAGI_POSTGRES_HOST', None)
        postgres_port = Config.value('ZIMAGI_POSTGRES_PORT', None)

    if postgres_host and postgres_port:
        DATABASES['default'] = {
            'ENGINE': 'systems.db.backends.postgresql',
            'NAME': postgres_db,
            'USER': postgres_user,
            'PASSWORD': postgres_password,
            'HOST': postgres_host,
            'PORT': postgres_port,
            'CONN_MAX_AGE': 120
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
                'CONN_MAX_AGE': 120
            }
        DATABASE_PROVIDER = 'postgres'
        DB_MAX_CONNECTIONS = Config.integer('ZIMAGI_DB_MAX_CONNECTIONS', 10)

DB_LOCK = threading.Semaphore(DB_MAX_CONNECTIONS)

#
# Redis configurations
#
redis_service = MANAGER.get_service(None, 'zimagi-redis')
redis_url = None

if redis_service:
    network_info = redis_service['ports']['6379/tcp'][0]
    redis_host = network_info["HostIp"]
    redis_port = network_info["HostPort"]
else:
    redis_host = Config.value('ZIMAGI_REDIS_HOST', None)
    redis_port = Config.value('ZIMAGI_REDIS_PORT', None)

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
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

if redis_url:
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
CACHE_MIDDLEWARE_SECONDS = Config.integer('ZIMAGI_PAGE_CACHE_SECONDS', 31536000) # 1 Year

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
SILENCED_SYSTEM_CHECKS = [
    'mysql.E001' # DBMutex lock_id over 255 chars (warning with MySQL)
]

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
COMMAND_PORT = Config.integer('ZIMAGI_COMMAND_PORT', 5123)
DATA_PORT = Config.integer('ZIMAGI_DATA_PORT', 5323)

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
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
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
