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
ROOT_URLCONF = 'services.command.urls'

REST_FRAMEWORK = {
    'UNAUTHENTICATED_USER': None,
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'systems.api.auth.EncryptedAPITokenAuthentication'
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated'
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'systems.api.schema.renderers.DataJSONRenderer'
    ]
}
