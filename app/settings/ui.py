"""
Application settings definition

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""
from .web import *
from .config import Config

import os
import importlib


#-------------------------------------------------------------------------------
# Core settings

#
# Application middleware
#
MIDDLEWARE = SECURITY_MIDDLEWARE + [
    'whitenoise.middleware.WhiteNoiseMiddleware'
] + INITIAL_MIDDLEWARE + MODULE_MIDDLEWARE + FINAL_MIDDLEWARE

#
# Static files
#
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(MANAGER.lib_path, 'static')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

#
# Rendering and display
#
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            *list(reversed(MANAGER.index.get_module_files('theme'))),
            os.path.join(APP_DIR, 'systems', 'forms', 'theme')
        ],
        'APP_DIRS': False,
        'OPTIONS': {}
    }
]

#-------------------------------------------------------------------------------
# Django Addons

#
# Site configuration
#
WSGI_APPLICATION = 'services.wsgi_ui.application'

CORS_ALLOW_METHODS = [
    'GET',
    'POST'
]

SECURE_CROSS_ORIGIN_OPENER_POLICY = Config.string('ZIMAGI_SECURE_CROSS_ORIGIN_OPENER_POLICY', 'unsafe-none')
SECURE_REFERRER_POLICY = Config.string('ZIMAGI_SECURE_REFERRER_POLICY', 'same-origin')

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
