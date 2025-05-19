"""
Application settings definition

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

import os
import threading

import colorful
from utility.filesystem import load_file

import zimagi

from .config import Config


class ConfigurationError(Exception):
    pass


# -------------------------------------------------------------------------------
# Core settings

#
# Directories
#
APP_DIR = "/usr/local/share/zimagi"
DATA_DIR = "/var/local/zimagi"
ROOT_LIB_DIR = "/usr/local/lib/zimagi"

HOST_APP_DIR = Config.value("ZIMAGI_HOST_APP_DIR", None)
HOST_DATA_DIR = Config.value("ZIMAGI_HOST_DATA_DIR", None)
HOST_LIB_DIR = Config.value("ZIMAGI_HOST_LIB_DIR", None)

VERSION = load_file(os.path.join(APP_DIR, "VERSION")).strip()

PROJECT_PATH_MAP_DYNAMIC = Config.dict("ZIMAGI_PROJECT_PATH_MAP", {})
PROJECT_PATH_MAP = {
    "dataset_path": "datasets",
    "st_model_cache": {
        "directory": "st_models",
        "backup": False,
    },
    "tr_model_cache": {
        "directory": "tr_models",
        "backup": False,
    },
    "hf_cache": {"directory": "hf_cache", "backup": False} ** PROJECT_PATH_MAP_DYNAMIC,
}

zimagi.settings.CACHE_DIR = DATA_DIR
zimagi.settings.CACHE_LIFETIME = Config.integer("ZIMAGI_CLIENT_CACHE_LIFETIME", 60)  # 24 hours (86400)

#
# Development
#
DEBUG = Config.boolean("ZIMAGI_DEBUG", False)
DEBUG_COMMAND_PROFILES = Config.boolean("ZIMAGI_DEBUG_COMMAND_PROFILES", False)

INIT_PROFILE = Config.boolean("ZIMAGI_INIT_PROFILE", False)
COMMAND_PROFILE = Config.boolean("ZIMAGI_COMMAND_PROFILE", False)
DISABLE_MODULE_INIT = Config.boolean("ZIMAGI_DISABLE_MODULE_INIT", False)
DISABLE_MODULE_SYNC = Config.boolean("ZIMAGI_DISABLE_MODULE_SYNC", False)
DISABLE_REMOVE_ERROR_MODULE = Config.boolean("ZIMAGI_DISABLE_REMOVE_ERROR_MODULE", False)

BASE_TEST_DIR = os.path.join(APP_DIR, "tests")
#
# General configurations
#
APP_NAME = Config.string("ZIMAGI_APP_NAME", "zimagi", default_on_empty=True)
APP_SERVICE = Config.string("ZIMAGI_SERVICE", "cli", default_on_empty=True)
APP_ENVIRONMENT = Config.string("ZIMAGI_ENVIRONMENT", "local", default_on_empty=True)

SECRET_KEY = Config.string("ZIMAGI_SECRET_KEY", "XXXXXX20181105")

ENCRYPT_COMMAND_API = Config.boolean("ZIMAGI_ENCRYPT_COMMAND_API", False)
ENCRYPT_MCP_API = Config.boolean("ZIMAGI_ENCRYPT_MCP_API", False)
ENCRYPT_DATA_API = Config.boolean("ZIMAGI_ENCRYPT_DATA_API", False)

PARALLEL = Config.boolean("ZIMAGI_PARALLEL", True)
THREAD_COUNT = Config.integer("ZIMAGI_THREAD_COUNT", 10)
QUEUE_COMMANDS = Config.boolean("ZIMAGI_QUEUE_COMMANDS", True)
FOLLOW_QUEUE_COMMAND = Config.boolean("ZIMAGI_FOLLOW_QUEUE_COMMAND", True)

NO_MIGRATE = Config.boolean("ZIMAGI_NO_MIGRATE", False)
AUTO_MIGRATE_TIMEOUT = Config.integer("ZIMAGI_AUTO_MIGRATE_TIMEOUT", 300)
AUTO_MIGRATE_INTERVAL = Config.integer("ZIMAGI_AUTO_MIGRATE_INTERVAL", 5)

TEST_PROCESS_COUNT = Config.integer("ZIMAGI_TEST_PROCESS_COUNT", 0)

ROLE_PROVIDER = Config.string("ZIMAGI_ROLE_PROVIDER", "role")

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Auto-populated by entrypoint scripts
# >>>
CLI_EXEC = Config.boolean("ZIMAGI_CLI_EXEC", False)
SERVICE_INIT = Config.boolean("ZIMAGI_SERVICE_INIT", False)
SERVICE_EXEC = Config.boolean("ZIMAGI_SERVICE_EXEC", False)
SCHEDULER_INIT = Config.boolean("ZIMAGI_SCHEDULER_INIT", False)
SCHEDULER_EXEC = Config.boolean("ZIMAGI_SCHEDULER_EXEC", False)
WORKER_INIT = Config.boolean("ZIMAGI_WORKER_INIT", False)
WORKER_EXEC = Config.boolean("ZIMAGI_WORKER_EXEC", False)
WSGI_INIT = Config.boolean("ZIMAGI_WSGI_INIT", False)
WSGI_EXEC = Config.boolean("ZIMAGI_WSGI_EXEC", False)
MCP_INIT = Config.boolean("ZIMAGI_MCP_INIT", False)
MCP_EXEC = Config.boolean("ZIMAGI_MCP_EXEC", False)
# <<<

#
# Time configuration
#
TIME_ZONE = "UTC"
USE_TZ = True

DEFAULT_DATE_FORMAT = Config.string("ZIMAGI_DEFAULT_DATE_FORMAT", "%Y-%m-%d")
DEFAULT_TIME_FORMAT = Config.string("ZIMAGI_DEFAULT_TIME_FORMAT", "%H:%M:%S")
DEFAULT_TIME_SPACER_FORMAT = Config.string("ZIMAGI_DEFAULT_TIME_SPACER_FORMAT", "T")

#
# Language configurations
#
LANGUAGE_CODE = Config.string("ZIMAGI_LOCALE", "en")
USE_I18N = True

#
# Display configurations
#
DISPLAY_LOCK = threading.Lock()

DISPLAY_WIDTH = Config.integer("ZIMAGI_DISPLAY_WIDTH", 120)
DISPLAY_COLOR = Config.boolean("ZIMAGI_DISPLAY_COLOR", True)
COLOR_SOLARIZED = Config.boolean("ZIMAGI_COLOR_SOLARIZED", True)

COMMAND_COLOR = Config.string("ZIMAGI_COMMAND_COLOR", "cyan")
HEADER_COLOR = Config.string("ZIMAGI_HEADER_COLOR", "violet")
KEY_COLOR = Config.string("ZIMAGI_KEY_COLOR", "cyan")
VALUE_COLOR = Config.string("ZIMAGI_VALUE_COLOR", "violet")
JSON_COLOR = Config.string("ZIMAGI_JSON_COLOR", "orange")
DYNAMIC_COLOR = Config.string("ZIMAGI_DYNAMIC_COLOR", "magenta")
RELATION_COLOR = Config.string("ZIMAGI_RELATION_COLOR", "green")
PREFIX_COLOR = Config.string("ZIMAGI_PREFIX_COLOR", "magenta")
SUCCESS_COLOR = Config.string("ZIMAGI_SUCCESS_COLOR", "green")
NOTICE_COLOR = Config.string("ZIMAGI_NOTICE_COLOR", "cyan")
WARNING_COLOR = Config.string("ZIMAGI_WARNING_COLOR", "orange")
ERROR_COLOR = Config.string("ZIMAGI_ERROR_COLOR", "red")
TRACEBACK_COLOR = Config.string("ZIMAGI_TRACEBACK_COLOR", "yellow")

colorful.use_true_colors()
if COLOR_SOLARIZED:
    colorful.use_style("solarized")

#
# Runtime configurations
#
os.environ["CURL_CA_BUNDLE"] = ""

BASE_DATA_PATH = os.path.join(DATA_DIR, "cli")
RUNTIME_PATH = f"{BASE_DATA_PATH}.yml"

DEFAULT_HOST_NAME = Config.string("ZIMAGI_DEFAULT_HOST_NAME", "default")
TEST_HOST_NAME = Config.string("ZIMAGI_TEST_HOST_NAME", "test")
DEFAULT_RUNTIME_IMAGE = Config.string("ZIMAGI_DEFAULT_RUNTIME_IMAGE", "zimagi/server:latest")
RUNTIME_IMAGE = Config.string("ZIMAGI_RUNTIME_IMAGE", DEFAULT_RUNTIME_IMAGE)

CORE_MODULE = Config.string("ZIMAGI_CORE_MODULE", "core")
DEFAULT_MODULES = Config.list("ZIMAGI_DEFAULT_MODULES", [])

RESTART_SERVICES = Config.boolean("ZIMAGI_RESTART_SERVICES", True)

#
# Docker configurations
#
DOCKER_RUNTIME = Config.string("ZIMAGI_DOCKER_RUNTIME", "standard")
DOCKER_USER_UID = Config.integer("ZIMAGI_USER_UID", 1010)
DOCKER_GID = Config.integer("ZIMAGI_DOCKER_GID", 0)

#
# Kubernetes configurations
#
KUBERNETES_NAMESPACE = Config.string("KUBERNETES_NAMESPACE", "")
KUBERNETES_SERVICE_ACCOUNT = Config.string("KUBERNETES_SERVICE_ACCOUNT", "")
KUBERNETES_WORKER_SERVICE_ACCOUNT = Config.string("KUBERNETES_WORKER_SERVICE_ACCOUNT", KUBERNETES_SERVICE_ACCOUNT)
KUBERNETES_NODE_NAME = Config.string("KUBERNETES_NODE_NAME", "")
KUBERNETES_POD_NAME = Config.string("KUBERNETES_POD_NAME", "")
KUBERNETES_POD_IP = Config.string("KUBERNETES_POD_IP", "")

KUBERNETES_IMAGE_PULL_SECRETS = Config.list("KUBERNETES_IMAGE_PULL_SECRETS", [])

KUBERNETES_LIB_PVC = Config.string("ZIMAGI_LIB_PVC", "lib")

KUBERNETES_GLOBAL_SECRET = Config.string("ZIMAGI_GLOBAL_SECRET", "global")
KUBERNETES_GLOBAL_CONFIG = Config.string("ZIMAGI_GLOBAL_CONFIG_MAP", "global")
KUBERNETES_SCHEDULER_CONFIG = Config.string("ZIMAGI_SCHEDULER_CONFIG_MAP", "scheduler")
KUBERNETES_CONTROLLER_CONFIG = Config.string("ZIMAGI_CONTROLLER_CONFIG_MAP", "controller")
KUBERNETES_WORKER_CONFIG = Config.string("ZIMAGI_WORKER_CONFIG_MAP", "worker")
KUBERNETES_COMMAND_CONFIG = Config.string("ZIMAGI_COMMAND_CONFIG_MAP", "command-api")
KUBERNETES_DATA_CONFIG = Config.string("ZIMAGI_DATA_CONFIG_MAP", "data-api")

KUBERNETES_SERVICE_CONFIGS = [KUBERNETES_COMMAND_CONFIG, KUBERNETES_DATA_CONFIG]

#
# Logging configuration
#
LOG_LEVEL = Config.string("ZIMAGI_LOG_LEVEL", "warning").upper()

zimagi.settings.LOG_LEVEL = LOG_LEVEL

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            "datefmt": "%d/%b/%Y %H:%M:%S",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        }
    },
    "loggers": {"": {"level": LOG_LEVEL, "handlers": ["console"]}},
}

LOG_RETENTION_DAYS = Config.integer("ZIMAGI_LOG_RETENTION_DAYS", 30)
LOG_MESSAGE_RETENTION_DAYS = Config.integer("ZIMAGI_LOG_MESSAGE_RETENTION_DAYS", 10)

#
# System check settings
#
SILENCED_SYSTEM_CHECKS = []

#
# Applications and libraries
#
INSTALLED_APPS = ["django.contrib.contenttypes", "django_dbconn_retry", "django.contrib.postgres", "settings.app.AppInit"]

MIDDLEWARE = ["django.middleware.security.SecurityMiddleware", "django.middleware.common.CommonMiddleware"]

#
# Authentication configuration
#
AUTH_USER_MODEL = "user.User"

TEMP_TOKEN_EXPIRATION = Config.integer("ZIMAGI_TEMP_TOKEN_EXPIRATION", 21600)  # 6 Hours

#
# API configuration
#
ADMIN_USER = Config.string("ZIMAGI_ADMIN_USER", "admin")
ADMIN_API_KEY = Config.string("ZIMAGI_ADMIN_API_KEY", None)
DEFAULT_ADMIN_TOKEN = Config.string("ZIMAGI_DEFAULT_ADMIN_TOKEN", "uy5c8xiahf93j2pl8s00e6nb32h87dn3")

ANONYMOUS_USER = Config.string("ZIMAGI_ANONYMOUS_USER", "anonymous")

#
# Worker configuration
#
WORKER_PROVIDER = Config.string("ZIMAGI_WORKER_PROVIDER", "docker")
WORKER_TIMEOUT = Config.integer("ZIMAGI_WORKER_TIMEOUT", 60)
WORKER_CHECK_INTERVAL = Config.integer("ZIMAGI_WORKER_CHECK_INTERVAL", 2)

WORKER_DEFAULT_TASK_PRIORITY = Config.integer("ZIMAGI_WORKER_DEFAULT_TASK_PRIORITY", 5)
WORKER_MAX_COUNT = Config.integer("ZIMAGI_WORKER_MAX_COUNT", 20)
AGENT_MAX_LIFETIME = Config.integer("ZIMAGI_AGENT_MAX_LIFETIME", 86400)

#
# Data configuration
#
FIELD_TYPE_MAP = Config.dict("ZIMAGI_FIELD_TYPE_MAP", {})

#
# OCR Processing
#
PDF_OCR_BATCH_SIZE = Config.integer("ZIMAGI_PDF_OCR_BATCH_SIZE", 10)
PDF_OCR_DPI = Config.integer("ZIMAGI_PDF_OCR_DPI", 200)

#
# GitHub configuration
#
GITHUB_TOKEN = Config.value("ZIMAGI_GITHUB_TOKEN", None)
GITHUB_ORG = Config.value("ZIMAGI_GITHUB_ORG", None)

#
# HuggingFace Account
#
HUGGINGFACE_TOKEN = Config.string("ZIMAGI_HUGGINGFACE_TOKEN")
