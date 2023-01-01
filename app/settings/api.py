"""
Application settings definition

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""
from .web import *
from .config import Config

import importlib


#-------------------------------------------------------------------------------
# Core settings

#-------------------------------------------------------------------------------
# Django Addons

#
# API configuration
#
WSGI_APPLICATION = 'services.wsgi_api.application'

REST_PAGE_COUNT = Config.integer('ZIMAGI_REST_PAGE_COUNT', 50)
REST_API_TEST = Config.boolean('ZIMAGI_REST_API_TEST', False)

CORS_ALLOW_METHODS = [
    'GET',
    'POST',
    'PUT',
    'DELETE'
]

SECURE_CROSS_ORIGIN_OPENER_POLICY = Config.string('ZIMAGI_SECURE_CROSS_ORIGIN_OPENER_POLICY', 'unsafe-none')
SECURE_REFERRER_POLICY = Config.string('ZIMAGI_SECURE_REFERRER_POLICY', 'no-referrer')

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

#-------------------------------------------------------------------------------
# Manager initialization

MANAGER.initialize()
