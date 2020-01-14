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
    'services.tasks'
] + INSTALLED_APPS

#-------------------------------------------------------------------------------
# Django Addons
