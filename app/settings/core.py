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
DEFAULT_RUNTIME_IMAGE = Config.string('DEFAULT_RUNTIME_IMAGE', 'cenv/cenv:latest')

#
# Database configurations
#
RUNTIME_PATH = "{}.env".format(os.path.join(DATA_DIR, Config.string('RUNTIME_FILE_NAME', 'cenv')))
RUNTIME_ENV = {}

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

#
# Applications and libraries
#
INSTALLED_APPS = [
    'utility',
    
    'data.user',
    'data.environment',
    'data.server',
    'data.storage',
    'data.project',
    
    'django.contrib.auth',
    'django.contrib.contenttypes',

    'db_mutex',
    'rest_framework',
    'rest_framework.authtoken'
]

MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware'    
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
ADMIN_GROUP = Config.string('ADMIN_GROUP', 'admin')
DEFAULT_ADMIN_TOKEN = Config.string('DEFAULT_ADMIN_TOKEN', 'a11223344556677889900z')

API_EXEC = False

#-------------------------------------------------------------------------------
# Cloud configurations

#
# Supported compute providers 
#
COMPUTE_PROVIDERS = {
    'man': 'systems.compute.Manual',
    'aws_ec2': 'systems.compute.AWSEC2'
}
for name, cls_str in Config.dict('COMPUTE_PROVIDERS').items():
    COMPUTE_PROVIDERS[name] = cls_str

#
# Supported storage providers 
#
STORAGE_PROVIDERS = {
    'man': 'systems.storage.Manual',
    'aws_efs': 'systems.storage.AWSEFS'
}
for name, cls_str in Config.dict('STORAGE_PROVIDERS').items():
    STORAGE_PROVIDERS[name] = cls_str

#-------------------------------------------------------------------------------
# Provisioning configurations

#
# Supported project providers 
#
PROJECT_PROVIDERS = {
    'git': 'systems.project.Git'
}
for name, cls_str in Config.dict('PROJECT_PROVIDERS').items():
    PROJECT_PROVIDERS[name] = cls_str

PROJECT_BASE_PATH = os.path.join(LIB_DIR, Config.string('PROJECTS_DIR', 'projects'))
pathlib.Path(PROJECT_BASE_PATH).mkdir(parents = True, exist_ok = True) 

#
# Supported provisioner providers 
#
PROVISIONER_PROVIDERS = {
    'ansible': 'systems.provisioner.Ansible'
}
for name, cls_str in Config.dict('PROVISIONER_PROVIDERS').items():
    PROVISIONER_PROVIDERS[name] = cls_str
