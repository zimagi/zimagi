"""
Application settings definition

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
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
