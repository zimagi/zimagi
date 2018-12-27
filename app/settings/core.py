"""
Django settings for the System administrative interface

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""
from utility.common import config_value

import os

#-------------------------------------------------------------------------------
# Global settings

#
# Directories
#
APP_DIR = '/usr/local/share/cenv'
DATA_DIR = '/var/local/cenv'

#-------------------------------------------------------------------------------
# Core Django settings

#
# Development
#
DEV_ENV = False

DEBUG = False
TEMPLATE_DEBUG = False

#
# General configurations
#
APP_NAME = 'ce'

SECRET_KEY = config_value('SECRET_KEY', 'XXXXXX20181105')

#
# Time configuration
#
TIME_ZONE = config_value('TIME_ZONE', 'EST')
USE_TZ = True

#
# Language configurations
#
LANGUAGE_CODE = 'en-us'
USE_I18N = True
USE_L10N = True

#
# Display configurations
#
DISPLAY_WIDTH = int(config_value('DISPLAY_WIDTH', 80))

#
# Database configurations
#
DATA_ENCRYPT = True
DATA_PATH = os.path.join(DATA_DIR, 'cenv.data')

DATABASES = {
    'default': {
        'ENGINE': 'systems.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
if config_value('POSTGRES_HOST', None) and config_value('POSTGRES_PORT', None):
    DATABASES['default'] = {
        'ENGINE': 'systems.db.backends.postgresql',
        'NAME': config_value('POSTGRES_DB', 'cenv'),
        'USER': config_value('POSTGRES_USER', 'cenv'),
        'PASSWORD': config_value('POSTGRES_PASSWORD', 'cenv'),
        'HOST': config_value('POSTGRES_HOST'),
        'PORT': config_value('POSTGRES_PORT')
    }

#
# Applications and libraries
#
INSTALLED_APPS = [
    'utility',
    
    'data.user',
    'data.environment',
    'data.server',
    
    'systems.command',
    
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',

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
# Templating configuration
#
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.tz',
                'django.contrib.auth.context_processors.auth',
            ],
        },
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
LOGLEVEL = config_value('LOGLEVEL', 'warning').upper()
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
            'level': LOGLEVEL,
            'handlers': ['console']
        }
    }
}

#-------------------------------------------------------------------------------
# Django Addons

#
# Mutex locking configuration
#
DB_MUTEX_TTL_SECONDS = 86400 # 1 day (24 hours)

#
# REST configuration 
#
WSGI_APPLICATION = 'services.api.wsgi.application'
ROOT_URLCONF = 'services.api.urls'
ALLOWED_HOSTS = ['*']

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

ADMIN_USER = config_value('ADMIN_USER', 'admin')
ADMIN_GROUP = config_value('ADMIN_GROUP', 'admin')
DEFAULT_ADMIN_TOKEN = config_value('DEFAULT_ADMIN_TOKEN', 'a11223344556677889900z')

#-------------------------------------------------------------------------------
# Cloud configurations

#
# AWS boto3 configuration 
#
AWS_ACCESS_KEY = config_value('AWS_ACCESS_KEY', None)
AWS_SECRET = config_value('AWS_SECRET', None)

#
# Supported providers 
#
CLOUD_PROVIDERS = {
    'bm': 'Physical',
    'aws': 'AWS'
}

#-------------------------------------------------------------------------------
#
# Local settings overrides
#
try:
    from settings.local import *
except:
    pass
