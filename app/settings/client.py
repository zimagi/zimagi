"""
Application settings definition

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

import os

from .config import Config  # noqa: F401
from .core import *  # noqa: F403

# -------------------------------------------------------------------------------
# Core settings

PROFILE_DIR = os.path.join(DATA_DIR, "profile")  # noqa: F405

#
# Applications and libraries
#
INSTALLED_APPS = []
MIDDLEWARE = []

#
# Template settings
#
TEMPLATES = []

# -------------------------------------------------------------------------------
# CLI client settings

COMMAND_HOST = Config.string("ZIMAGI_COMMAND_HOST", "localhost")
COMMAND_PORT = Config.integer("ZIMAGI_COMMAND_PORT", 5123)

DATA_HOST = Config.string("ZIMAGI_DATA_HOST", "localhost")
DATA_PORT = Config.integer("ZIMAGI_DATA_PORT", 5123)

API_USER = Config.string("ZIMAGI_API_USER", ADMIN_USER)  # noqa: F405
API_USER_TOKEN = Config.string("ZIMAGI_API_USER_TOKEN", DEFAULT_ADMIN_TOKEN)  # noqa: F405
API_USER_KEY = Config.string("ZIMAGI_API_USER_KEY", ADMIN_API_KEY)  # noqa: F405
