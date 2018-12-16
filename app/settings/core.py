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
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJ_DIR = os.path.dirname(BASE_DIR)

#-------------------------------------------------------------------------------
# Core Django settings

#
# Debugging
#
DEBUG = False
TEMPLATE_DEBUG = False

#
# General configurations
#
APP_NAME = 'ce'

SECRET_KEY = config_value('SECRET_KEY', 'XXXXXX20181118')

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
DISPLAY_WIDTH = config_value('DISPLAY_WIDTH', 80)

#
# Database configurations
#
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(PROJ_DIR, 'app/db/data.db'),
    }
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
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt' : "%d/%b/%Y %H:%M:%S"
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
        'csv': {
            'format' : '"%(asctime)s","%(levelname)s",%(message)s',
            'datefmt' : "%Y-%m-%d %H:%M:%S"
        }
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class':'logging.NullHandler'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(PROJ_DIR, 'logs/django.log'),
            'formatter': 'verbose'
        },
        'memory_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(PROJ_DIR, 'logs/memory.csv'),
            'formatter': 'csv'
        },
        'data_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(PROJ_DIR, 'logs/data.csv'),
            'formatter': 'csv'
        }
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['null'],
            'propagate': False,
            'level':'DEBUG'
        },
        'django': {
            'handlers':['file'],
            'propagate': True,
            'level':'DEBUG'
        },
        'memory': {
            'handlers': ['memory_file'],
            'level': 'INFO'
        },
        'data': {
            'handlers': ['data_file'],
            'level': 'INFO'
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
        'rest_framework.authentication.TokenAuthentication'
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
        'systems.api.auth.CommandPermission'
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer'
    ]
}

API_URL = config_value('API_URL', 'http://localhost:5120')
API_TOKEN = config_value('API_TOKEN', None)

#-------------------------------------------------------------------------------
#
# Local settings overrides
#
try:
    from settings.local import *
except:
    pass
