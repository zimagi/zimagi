"""
Application settings definition

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

import importlib

from systems.manager import Manager

from .core import *  # noqa: F403

# -------------------------------------------------------------------------------
# Core settings

MANAGER = Manager()  # noqa: F405

#
# Applications and libraries
#
INSTALLED_APPS = ["settings.app.AppInit"]

# -------------------------------------------------------------------------------
# Service specific settings

service_module = importlib.import_module(f"services.{APP_SERVICE}.settings")  # noqa: F405
for setting in dir(service_module):
    if setting == setting.upper():
        locals()[setting] = getattr(service_module, setting)

# -------------------------------------------------------------------------------
# External module settings

for settings_module in MANAGER.index.get_settings_modules():
    for setting in dir(settings_module):
        if setting == setting.upper():
            locals()[setting] = getattr(settings_module, setting)

# -------------------------------------------------------------------------------
# Manager initialization

MANAGER.initialize()
