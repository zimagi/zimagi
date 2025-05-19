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
ROOT_URLCONF = "services.data.urls"

REST_FRAMEWORK = {
    "UNAUTHENTICATED_USER": None,
    "DEFAULT_SCHEMA_CLASS": "systems.api.data.schema.DataSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": ["systems.api.data.auth.DataAPITokenAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["systems.api.data.auth.DataPermission"],
    "DEFAULT_PARSER_CLASSES": ["systems.api.data.parsers.JSONParser"],
    "DEFAULT_RENDERER_CLASSES": ["systems.api.renderers.JSONRenderer"],
    "DEFAULT_FILTER_BACKENDS": [],
    "SEARCH_PARAM": "q",
    "COERCE_DECIMAL_TO_STRING": False,
    "DATE_FORMAT": "%Y-%m-%d",
    "DATE_INPUT_FORMATS": ["%Y-%m-%d"],
    "DATETIME_FORMAT": "%Y-%m-%dT%H:%M:%S",
    "DATETIME_INPUT_FORMATS": ["%Y-%m-%dT%H:%M:%S"],
    "TIME_FORMAT": "%H:%M:%S",
    "TIME_INPUT_FORMATS": ["%H:%M:%S"],
}

LIMIT_PARAM = "limit"
FIELDS_PARAM = "fields"
