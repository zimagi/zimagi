"""
Application settings definition

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

import importlib
import os
import re
import threading

from django.template import base

from .config import Config
from .core import *  # noqa: F403

# -------------------------------------------------------------------------------
# Core settings

MANAGER = Manager()  # noqa: F405

#
# Service configuration
#
try:
    SERVICE_ID = MANAGER.container_id
except Exception:
    SERVICE_ID = KUBERNETES_POD_NAME  # noqa: F405

#
# Applications and libraries
#
INSTALLED_APPS = MANAGER.index.get_installed_apps() + [
    "django.contrib.contenttypes",
    "django_dbconn_retry",
    "django.contrib.postgres",
    "rest_framework",
    "django_filters",
    "corsheaders",
    "settings.app.AppInit",
]

MIDDLEWARE = (
    [
        "django.middleware.security.SecurityMiddleware",
        "corsheaders.middleware.CorsMiddleware",
        "django.middleware.common.CommonMiddleware",
        "systems.cache.middleware.UpdateCacheMiddleware",
    ]
    + MANAGER.index.get_installed_middleware()
    + ["systems.cache.middleware.FetchCacheMiddleware"]
)

#
# Template settings
#
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(module_dir, "django", "templates") for module_dir in MANAGER.index.get_module_dirs()],
        "APP_DIRS": False,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.i18n",
                "django.template.context_processors.tz",
                *Config.list("ZIMAGI_DJANGO_TEMPLATE_PROCESSORS", []),
            ]
        },
    }
]

# Multi-line template tags: https://stackoverflow.com/a/54206609
base.tag_re = re.compile(base.tag_re.pattern, re.DOTALL)

#
# Database configurations
#
DB_PACKAGE_ALL_NAME = Config.string("ZIMAGI_DB_PACKAGE_ALL_NAME", "all")
DATABASE_ROUTERS = ["systems.db.router.DatabaseRouter"]

postgres_service = MANAGER.get_service("postgresql")
postgres_service_port = postgres_service["ports"]["5432/tcp"] if postgres_service else None

if postgres_service:
    postgres_host = "127.0.0.1"
    postgres_port = postgres_service_port
else:
    postgres_host = None
    postgres_port = None

_postgres_host = Config.value("ZIMAGI_POSTGRES_HOST", None)
if _postgres_host:
    postgres_host = _postgres_host

_postgres_port = Config.value("ZIMAGI_POSTGRES_PORT", None)
if _postgres_port:
    postgres_port = _postgres_port

if not postgres_host or not postgres_port:
    raise ConfigurationError("ZIMAGI_POSTGRES_HOST and ZIMAGI_POSTGRES_PORT environment variables required")  # noqa: F405

postgres_db = Config.string("ZIMAGI_POSTGRES_DB", "zimagi")
postgres_user = Config.string("ZIMAGI_POSTGRES_USER", "postgres")
postgres_password = Config.string("ZIMAGI_POSTGRES_PASSWORD", "zimagi")
postgres_write_port = Config.value("ZIMAGI_POSTGRES_WRITE_PORT", None)

DATABASES = {
    "default": {
        "ENGINE": "systems.db.backends.postgresql",
        "NAME": postgres_db,
        "USER": postgres_user,
        "PASSWORD": postgres_password,
        "HOST": postgres_host,
        "PORT": postgres_port,
        "CONN_MAX_AGE": None,
    }
}
if postgres_write_port:
    postgres_write_host = Config.value("ZIMAGI_POSTGRES_WRITE_HOST", postgres_host)

    DATABASES["write"] = {
        "ENGINE": "systems.db.backends.postgresql",
        "NAME": postgres_db,
        "USER": postgres_user,
        "PASSWORD": postgres_password,
        "HOST": postgres_write_host,
        "PORT": postgres_write_port,
        "CONN_MAX_AGE": 1,
    }

DISABLE_SERVER_SIDE_CURSORS = True
DB_MAX_CONNECTIONS = Config.integer("ZIMAGI_DB_MAX_CONNECTIONS", 100)
DB_LOCK = threading.Semaphore(DB_MAX_CONNECTIONS)

DB_SNAPSHOT_RENTENTION = Config.integer("ZIMAGI_DB_SNAPSHOT_RENTENTION", 3)

#
# Redis configurations
#
redis_service = MANAGER.get_service("redis")

if redis_service:
    redis_host = "127.0.0.1"
    redis_port = redis_service["ports"]["6379/tcp"]
else:
    redis_host = None
    redis_port = None

_redis_host = Config.value("ZIMAGI_REDIS_HOST", None)
if _redis_host:
    redis_host = _redis_host

_redis_port = Config.value("ZIMAGI_REDIS_PORT", None)
if _redis_port:
    redis_port = _redis_port

redis_url = None

if redis_host and redis_port:
    redis_protocol = Config.string("ZIMAGI_REDIS_TYPE", "redis")
    redis_password = Config.value("ZIMAGI_REDIS_PASSWORD")

    if redis_password:
        redis_url = f"{redis_protocol}://:{redis_password}@{redis_host}:{redis_port}"
    else:
        redis_url = f"{redis_protocol}://{redis_host}:{redis_port}"

#
# Process Management
#
if redis_url:
    REDIS_TASK_URL = f"{redis_url}/2"
else:
    REDIS_TASK_URL = None
    QUEUE_COMMANDS = False

#
# Database mutex locking
#
if redis_url:
    REDIS_MUTEX_URL = f"{redis_url}/3"
else:
    REDIS_MUTEX_URL = None

MUTEX_TTL_SECONDS = Config.integer("ZIMAGI_MUTEX_TTL_SECONDS", 432000)

#
# Communications
#
if redis_url:
    REDIS_COMMUNICATION_URL = f"{redis_url}/4"
else:
    REDIS_COMMUNICATION_URL = None

#
# Caching configuration
#
CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"},
    "page": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"},
}

if redis_url and not Config.boolean("ZIMAGI_DISABLE_PAGE_CACHE", False):
    CACHES["page"] = {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"{redis_url}/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "IGNORE_EXCEPTIONS": True,
            "PARSER_CLASS": "redis.connection._HiredisParser",
        },
    }

CACHE_MIDDLEWARE_ALIAS = "page"
CACHE_MIDDLEWARE_KEY_PREFIX = ""
CACHE_MIDDLEWARE_SECONDS = Config.integer("ZIMAGI_PAGE_CACHE_SECONDS", 86400)  # 1 Day

CACHE_PARAM = "refresh"

#
# Email configuration
#
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = Config.value("ZIMAGI_EMAIL_HOST", None)
EMAIL_PORT = Config.integer("ZIMAGI_EMAIL_PORT", 25)
EMAIL_HOST_USER = Config.string("ZIMAGI_EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = Config.string("ZIMAGI_EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = Config.boolean("ZIMAGI_EMAIL_USE_TLS", True)
EMAIL_USE_SSL = Config.boolean("ZIMAGI_EMAIL_USE_SSL", False)
EMAIL_SSL_CERTFILE = Config.value("ZIMAGI_EMAIL_SSL_CERTFILE", None)
EMAIL_SSL_KEYFILE = Config.value("ZIMAGI_EMAIL_SSL_KEYFILE", None)
EMAIL_TIMEOUT = Config.value("ZIMAGI_EMAIL_TIMEOUT", None)
EMAIL_SUBJECT_PREFIX = Config.string("ZIMAGI_EMAIL_SUBJECT_PREFIX", "[Zimagi]>")
EMAIL_USE_LOCALTIME = Config.boolean("ZIMAGI_EMAIL_USE_LOCALTIME", True)

# -------------------------------------------------------------------------------
# Django Addons

#
# API configuration
#
WSGI_APPLICATION = "services.wsgi.application"

ALLOWED_HOSTS = Config.list("ZIMAGI_ALLOWED_HOSTS", ["*"])

REST_PAGE_COUNT = Config.integer("ZIMAGI_REST_PAGE_COUNT", 50)
REST_API_TEST = Config.boolean("ZIMAGI_REST_API_TEST", False)

CORS_ALLOWED_ORIGINS = Config.list("ZIMAGI_CORS_ALLOWED_ORIGINS", [])
CORS_ALLOWED_ORIGIN_REGEXES = Config.list("ZIMAGI_CORS_ALLOWED_ORIGIN_REGEXES", [])
CORS_ALLOW_ALL_ORIGINS = Config.boolean("ZIMAGI_CORS_ALLOW_ALL_ORIGINS", True)

CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "DELETE"]

SECURE_CROSS_ORIGIN_OPENER_POLICY = Config.string("ZIMAGI_SECURE_CROSS_ORIGIN_OPENER_POLICY", "unsafe-none")
SECURE_REFERRER_POLICY = Config.string("ZIMAGI_SECURE_REFERRER_POLICY", "no-referrer")

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

MCP_SERVICE_NAME = Config.string("ZIMAGI_MCP_SERVICE_NAME", "mcp-api")
MCP_LOCAL_SERVER_NAME = Config.string("ZIMAGI_MCP_LOCAL_SERVER_NAME", "local")

#
# Celery
#
CELERY_TIMEZONE = TIME_ZONE  # noqa: F405
CELERY_ACCEPT_CONTENT = ["application/json"]

CELERY_BROKER_TRANSPORT_OPTIONS = {
    "master_name": "zimagi",
    "visibility_timeout": Config.decimal("ZIMAGI_CELERY_VISIBILITY_TIMEOUT", 43200),
}
CELERY_BROKER_URL = f"{redis_url}/0" if redis_url else None
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BROKER_CONNECTION_MAX_RETRIES = Config.integer("ZIMAGI_CELERY_CONNECTION_MAX_RETRIES", 10)

CELERY_WORKER_POOL_RESTARTS = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_CREATE_MISSING_QUEUES = True
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_SERIALIZER = "json"
CELERY_TASK_ROUTES = {"celery.*": "default", "zimagi.notification.*": "default"}

CELERY_BEAT_SCHEDULE = {}

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
