"""
For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

# -------------------------------------------------------------------------------
# Global settings

#
# Display configurations
#
DISPLAY_COLOR = False

# -------------------------------------------------------------------------------
# Core Django settings

# -------------------------------------------------------------------------------
# Django Addons

#
# API configuration
#
ROOT_URLCONF = "services.command.urls"

REST_FRAMEWORK = {
    "UNAUTHENTICATED_USER": None,
    "DEFAULT_SCHEMA_CLASS": "systems.api.command.schema.CommandSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": ["systems.api.command.auth.CommandAPITokenAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["systems.api.command.auth.CommandPermission"],
    "DEFAULT_RENDERER_CLASSES": ["systems.api.renderers.JSONRenderer"],
}
