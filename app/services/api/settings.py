"""
Django settings for the Command line utility, see
https://docs.djangoproject.com/en/2.1/topics/settings/
For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""
from settings.core import *

import os

#-------------------------------------------------------------------------------
# Global settings

#-------------------------------------------------------------------------------
# Core Django settings

#
# Server configurations
#
WSGI_APPLICATION = 'services.api.wsgi.application'
ROOT_URLCONF = 'services.api.urls'

ALLOWED_HOSTS = [
    '*',
]

#
# Applications and libraries
#
INSTALLED_APPS = [
    'services.api'
] + INSTALLED_APPS

#-------------------------------------------------------------------------------
# Django Addons
