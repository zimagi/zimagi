"""
For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""
from settings.core import *

import os

#-------------------------------------------------------------------------------
# Global settings

#-------------------------------------------------------------------------------
# Core Django settings

#
# Applications and libraries
#
INSTALLED_APPS = [
    'services.data'
] + INSTALLED_APPS

#-------------------------------------------------------------------------------
# Django Addons

#
# API configuration
#
WSGI_APPLICATION = 'services.data.wsgi.application'
ROOT_URLCONF = 'services.data.urls'

REST_FRAMEWORK = {
    'UNAUTHENTICATED_USER': None,
    'DEFAULT_SCHEMA_CLASS': 'systems.api.schema.data.DataSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # 'systems.api.auth.EncryptedAPITokenAuthentication'
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        # 'rest_framework.permissions.IsAuthenticated'
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer'
    ],
    'DEFAULT_FILTER_BACKENDS': [],
    'SEARCH_PARAM': 'q',
    'COERCE_DECIMAL_TO_STRING': False
}
