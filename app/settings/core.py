"""
Django settings for the System administrative interface

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""
from utility.config import Config

import os
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
DEBUG = Config.boolean('DEBUG', False)

#
# General configurations
#
APP_NAME = 'ce'

SECRET_KEY = Config.string('SECRET_KEY', 'XXXXXX20181105')

PARALLEL = Config.boolean('PARALLEL', True)
WORKER_COUNT = Config.integer('WORKER_COUNT', 10)

#
# Time configuration
#
TIME_ZONE = Config.string('TIME_ZONE', 'EST')
USE_TZ = True

#
# Language configurations
#
LANGUAGE_CODE = Config.string('LOCALE', 'en-us')
USE_I18N = True
USE_L10N = True

#
# Display configurations
#
DISPLAY_WIDTH = Config.integer('DISPLAY_WIDTH', 80)

#
# Runtime configurations
#
DEFAULT_ENV_NAME = Config.string('DEFAULT_ENV_NAME', 'default')
DEFAULT_RUNTIME_REPO = Config.string('DEFAULT_RUNTIME_REPO', 'registry.hub.docker.com')
DEFAULT_RUNTIME_IMAGE = Config.string('DEFAULT_RUNTIME_IMAGE', 'cenv/cenv:latest')

#
# Database configurations
#
RUNTIME_PATH = "{}.env".format(os.path.join(DATA_DIR, Config.string('RUNTIME_FILE_NAME', 'cenv')))

DATA_ENCRYPT = Config.boolean('DATA_ENCRYPT', True)
BASE_DATA_PATH = os.path.join(DATA_DIR, Config.string('DATA_FILE_NAME', 'cenv'))

DATABASES = {
    'default': {
        'ENGINE': 'systems.db.backends.sqlite3'
    }
}
if Config.value('POSTGRES_HOST', None) and Config.value('POSTGRES_PORT', None):
    DATABASES['default'] = {
        'ENGINE': 'systems.db.backends.postgresql',
        'NAME': Config.string('POSTGRES_DB', 'cenv'),
        'USER': Config.string('POSTGRES_USER', 'cenv'),
        'PASSWORD': Config.string('POSTGRES_PASSWORD', 'cenv'),
        'HOST': Config.string('POSTGRES_HOST'),
        'PORT': Config.integer('POSTGRES_PORT')
    }

DB_LOCK = threading.Lock()

#
# Applications and libraries
#
INSTALLED_APPS = [
    'interface',
    'utility',

    'data.user',
    'data.environment',
    'data.state',
    'data.log',
    'data.group',    
    'data.config',
    'data.project',
    'data.network',
    'data.subnet',
    'data.firewall',
    'data.firewall_rule',
    'data.storage',
    'data.storage_mount',
    'data.server',
        
    'django.contrib.contenttypes',
    'rest_framework',
    'db_mutex'    
]

MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
    'django.middleware.security.SecurityMiddleware'    
]

#
# Authentication configuration
#
AUTH_USER_MODEL = 'user.User'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

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
LOG_LEVEL = Config.string('LOG_LEVEL', 'warning').upper()
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
# Mutex locking configuration
#
DB_MUTEX_TTL_SECONDS = Config.integer('MUTEX_TTL_SEC', 86400) # 1 day (24 hours)

#
# REST configuration 
#
WSGI_APPLICATION = 'services.api.wsgi.application'
ROOT_URLCONF = 'services.api.urls'
ALLOWED_HOSTS = Config.list('ALLOWED_HOSTS', ['*'])

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

ADMIN_USER = Config.string('ADMIN_USER', 'admin')
DEFAULT_ADMIN_TOKEN = Config.string('DEFAULT_ADMIN_TOKEN', 'a11223344556677889900z')

API_EXEC = False

#-------------------------------------------------------------------------------
# Core provider configurations

#
# Supported user providers 
#
USER_PROVIDERS = {
    'internal': 'systems.user.Internal'
}
for name, cls_str in Config.dict('USER_PROVIDERS').items():
    USER_PROVIDERS[name] = cls_str

#
# Supported environment providers 
#
ENVIRONMENT_PROVIDERS = {
    'internal': 'systems.environment.Internal'
}
for name, cls_str in Config.dict('ENVIRONMENT_PROVIDERS').items():
    ENVIRONMENT_PROVIDERS[name] = cls_str

#
# Supported group providers 
#
GROUP_PROVIDERS = {
    'internal': 'systems.group.Internal'
}
for name, cls_str in Config.dict('GROUP_PROVIDERS').items():
    GROUP_PROVIDERS[name] = cls_str

#
# Supported configuration providers 
#
CONFIG_PROVIDERS = {
    'internal': 'systems.config.Internal'
}
for name, cls_str in Config.dict('CONFIG_PROVIDERS').items():
    CONFIG_PROVIDERS[name] = cls_str


#-------------------------------------------------------------------------------
# Cloud configurations

#
# Supported federation providers 
#
FEDERATION_PROVIDERS = {
    'internal': 'systems.federation.Internal'
}
for name, cls_str in Config.dict('FEDERATION_PROVIDERS').items():
    FEDERATION_PROVIDERS[name] = cls_str

#
# Supported network providers 
#
NETWORK_PROVIDERS = {
    'internal': 'systems.network.Internal',
    'aws': 'systems.network.AWS'
}
for name, cls_str in Config.dict('NETWORK_PROVIDERS').items():
    NETWORK_PROVIDERS[name] = cls_str

#
# Supported storage providers 
#
STORAGE_PROVIDERS = {
    'internal': 'systems.storage.Internal',
    'efs': 'systems.storage.AWSEFS'
}
for name, cls_str in Config.dict('STORAGE_PROVIDERS').items():
    STORAGE_PROVIDERS[name] = cls_str

#
# Supported server providers 
#
SERVER_PROVIDERS = {
    'internal': 'systems.compute.Internal',
    'ec2': 'systems.compute.AWSEC2'
}
for name, cls_str in Config.dict('SERVER_PROVIDERS').items():
    SERVER_PROVIDERS[name] = cls_str

#-------------------------------------------------------------------------------
# Provisioning configurations

#
# Supported project providers 
#
PROJECT_PROVIDERS = {
    'internal': 'systems.project.Internal',
    'git': 'systems.project.Git'
}
for name, cls_str in Config.dict('PROJECT_PROVIDERS').items():
    PROJECT_PROVIDERS[name] = cls_str

PROJECT_BASE_PATH = os.path.join(LIB_DIR, Config.string('PROJECTS_DIR', 'projects'))
pathlib.Path(PROJECT_BASE_PATH).mkdir(mode = 0o700, parents = True, exist_ok = True) 

CORE_PROJECT = Config.string('CORE_PROJECT', 'core')

#
# Supported project task execution providers 
#
TASK_PROVIDERS = {
    'command': 'systems.task.Command',
    'upload': 'systems.task.Upload',
    'script': 'systems.task.Script',
    'ansible': 'systems.task.Ansible'
}
for name, cls_str in Config.dict('TASK_PROVIDERS').items():
    TASK_PROVIDERS[name] = cls_str

#
# Terraform configuration 
#
TERRAFORM_LOCK = threading.Lock()
