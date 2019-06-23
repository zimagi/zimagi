"""
Application settings definition

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""
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
APP_DIR = '/usr/local/share/cenv'
DATA_DIR = '/var/local/cenv'
LIB_DIR = '/usr/local/lib/cenv'

#-------------------------------------------------------------------------------
# Core Django settings

#
# Development
#
DEBUG = Config.boolean('CENV_DEBUG', False)

#
# General configurations
#
APP_NAME = 'ce'

SECRET_KEY = Config.string('CENV_SECRET_KEY', 'XXXXXX20181105')

PARALLEL = Config.boolean('CENV_PARALLEL', True)
THREAD_COUNT = Config.integer('CENV_THREAD_COUNT', 5)

#
# Time configuration
#
TIME_ZONE = Config.string('CENV_TIME_ZONE', 'America/New_York')
USE_TZ = True

#
# Language configurations
#
LANGUAGE_CODE = Config.string('CENV_LOCALE', 'en-us')
USE_I18N = True
USE_L10N = True

#
# Display configurations
#
DISPLAY_WIDTH = Config.integer('CENV_DISPLAY_WIDTH', 80)
DISPLAY_COLOR = Config.boolean('CENV_DISPLAY_COLOR', True)
COLOR_SOLARIZED = Config.boolean('CENV_COLOR_SOLARIZED', True)

COMMAND_COLOR = Config.string('CENV_COMMAND_COLOR', 'cyan')
HEADER_COLOR = Config.string('CENV_HEADER_COLOR', 'violet')
KEY_COLOR = Config.string('CENV_KEY_COLOR', 'cyan')
VALUE_COLOR = Config.string('CENV_VALUE_COLOR', 'violet')
ENCRYPTED_COLOR = Config.string('CENV_ENCRYPTED_COLOR', 'yellow')
DYNAMIC_COLOR = Config.string('CENV_DYNAMIC_COLOR', 'magenta')
RELATION_COLOR = Config.string('CENV_RELATION_COLOR', 'green')
PREFIX_COLOR = Config.string('CENV_PREFIX_COLOR', 'magenta')
SUCCESS_COLOR = Config.string('CENV_SUCCESS_COLOR', 'green')
NOTICE_COLOR = Config.string('CENV_NOTICE_COLOR', 'cyan')
WARNING_COLOR = Config.string('CENV_WARNING_COLOR', 'orange')
ERROR_COLOR = Config.string('CENV_ERROR_COLOR', 'red')
TRACEBACK_COLOR = Config.string('CENV_TRACEBACK_COLOR', 'yellow')

#
# Runtime configurations
#
RUNTIME_PATH = "{}.env".format(os.path.join(DATA_DIR, Config.string('CENV_RUNTIME_FILE_NAME', 'cenv')))

DEFAULT_ENV_NAME = Config.string('CENV_DEFAULT_ENV_NAME', 'default')
DEFAULT_HOST_NAME = Config.string('CENV_DEFAULT_HOST_NAME', 'default')
DEFAULT_RUNTIME_REPO = Config.string('CENV_DEFAULT_RUNTIME_REPO', 'registry.hub.docker.com')
DEFAULT_RUNTIME_IMAGE = Config.string('CENV_DEFAULT_RUNTIME_IMAGE', 'cenv/cenv:latest')

MODULE_BASE_PATH = os.path.join(LIB_DIR, Config.string('CENV_MODULES_DIR', 'modules'))
pathlib.Path(MODULE_BASE_PATH).mkdir(mode = 0o700, parents = True, exist_ok = True)

CORE_MODULE = Config.string('CENV_CORE_MODULE', 'core')
DEFAULT_MODULES = Config.dict('CENV_DEFAULT_MODULES', {})

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
BASE_DATA_PATH = os.path.join(DATA_DIR, Config.string('CENV_DATA_FILE_NAME', 'cenv'))
DATABASE_PROVIDER = 'sqlite'

DB_MAX_CONNECTIONS = 1
DB_PACKAGE_ALL_NAME = Config.string('CENV_DB_PACKAGE_ALL_NAME', 'all')

DATABASES = {
    'default': {
        'ENGINE': 'systems.db.backends.sqlite3',
        'OPTIONS': {
            'timeout': 30 # secs
        }
    }
}

mysql_host = Config.value('CENV_MYSQL_HOST', None)
mysql_port = Config.value('CENV_MYSQL_PORT', None)

if mysql_host and mysql_port:
    DATABASES['default'] = {
        'ENGINE': 'systems.db.backends.mysql',
        'NAME': Config.string('CENV_MYSQL_DB', 'cenv'),
        'USER': Config.string('CENV_MYSQL_USER', 'cenv'),
        'PASSWORD': Config.string('CENV_MYSQL_PASSWORD', 'cenv'),
        'HOST': mysql_host,
        'PORT': mysql_port
    }
    DATABASE_PROVIDER = 'mysql'
    DB_MAX_CONNECTIONS = Config.integer('CENV_DB_MAX_CONNECTIONS', 1)
else:
    postgres_service = MANAGER.get_service(None, 'cenv-postgres')
    if postgres_service:
        network_info = postgres_service['ports']['5432/tcp'][0]
        postgres_host = network_info["HostIp"]
        postgres_port = network_info["HostPort"]
    else:
        postgres_host = Config.value('CENV_POSTGRES_HOST', None)
        postgres_port = Config.value('CENV_POSTGRES_PORT', None)

    if postgres_host and postgres_port:
        DATABASES['default'] = {
            'ENGINE': 'systems.db.backends.postgresql',
            'NAME': Config.string('CENV_POSTGRES_DB', 'cenv'),
            'USER': Config.string('CENV_POSTGRES_USER', 'cenv'),
            'PASSWORD': Config.string('CENV_POSTGRES_PASSWORD', 'cenv'),
            'HOST': postgres_host,
            'PORT': postgres_port
        }
        DATABASE_PROVIDER = 'postgres'
        DB_MAX_CONNECTIONS = Config.integer('CENV_DB_MAX_CONNECTIONS', 1)

DB_LOCK = threading.Semaphore(DB_MAX_CONNECTIONS)

#
# Applications and libraries
#
INSTALLED_APPS = MANAGER.installed_apps() + [
    'django.contrib.contenttypes',
    'rest_framework'
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
LOG_LEVEL = Config.string('CENV_LOG_LEVEL', 'warning').upper()
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

#-------------------------------------------------------------------------------
# Django Addons

#
# API configuration
#
API_INIT = Config.boolean('CENV_API_INIT', False)
API_EXEC = Config.boolean('CENV_API_EXEC', False)

WSGI_APPLICATION = 'services.api.wsgi.application'
ROOT_URLCONF = 'services.api.urls'
ALLOWED_HOSTS = Config.list('CENV_ALLOWED_HOSTS', ['*'])

REST_FRAMEWORK = {
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

ADMIN_USER = Config.string('CENV_ADMIN_USER', 'admin')
DEFAULT_ADMIN_TOKEN = Config.string('CENV_DEFAULT_ADMIN_TOKEN', 'a11223344556677889900z')

#-------------------------------------------------------------------------------
# External module settings

for settings_module in MANAGER.settings_modules():
    for setting in dir(settings_module):
        if setting == setting.upper():
            locals()[setting] = getattr(settings_module, setting)
