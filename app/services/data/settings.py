"""
For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""
#-------------------------------------------------------------------------------
# Global settings

#
# Display configurations
#
DISPLAY_COLOR = False

#-------------------------------------------------------------------------------
# Core Django settings

#-------------------------------------------------------------------------------
# Django Addons

#
# API configuration
#
ROOT_URLCONF = 'services.data.urls'

REST_FRAMEWORK = {
    'UNAUTHENTICATED_USER': None,
    'DEFAULT_SCHEMA_CLASS': 'systems.api.schema.data.DataSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'systems.api.auth.DataAPITokenAuthentication'
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'systems.api.auth.DataPermission'
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'systems.api.schema.renderers.DataJSONRenderer'
    ],
    'DEFAULT_FILTER_BACKENDS': [],
    'SEARCH_PARAM': 'q',
    'COERCE_DECIMAL_TO_STRING': False
}
