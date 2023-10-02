"""
Application settings definition

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""
from .core import *

import importlib


#-------------------------------------------------------------------------------
# Core settings

MANAGER = Manager()

#
# Applications and libraries
#
INSTALLED_APPS = ['settings.app.AppInit']

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
