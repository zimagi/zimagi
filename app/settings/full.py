"""
Application settings definition

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""
from .core import *
from .config import Config

import threading


#-------------------------------------------------------------------------------
# Core settings

MANAGER = Manager()

#
# Applications and libraries (ALL APPS MUST BE LOADED FOR EVERY SERVICE)
#
INSTALLED_APPS = MANAGER.index.get_installed_apps() + [
    'django_dbconn_retry',
    'django.contrib.postgres',
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'rest_framework',
    'django_filters',
    'corsheaders',
    'systems.forms',
    'settings.app.AppInit'
]

#
# Application middleware
#
SECURITY_MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware'
]
INITIAL_MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
    'systems.cache.middleware.UpdateCacheMiddleware'
]
MODULE_MIDDLEWARE = MANAGER.index.get_installed_middleware()
FINAL_MIDDLEWARE = [
    'systems.cache.middleware.FetchCacheMiddleware'
]

MIDDLEWARE = SECURITY_MIDDLEWARE + \
             INITIAL_MIDDLEWARE + \
             MODULE_MIDDLEWARE + \
             FINAL_MIDDLEWARE

#
# Database configurations
#
DB_PACKAGE_ALL_NAME = Config.string('ZIMAGI_DB_PACKAGE_ALL_NAME', 'all')
DATABASE_ROUTERS = ['systems.db.router.DatabaseRouter']

postgres_service = MANAGER.get_service('postgresql')
postgres_service_port = postgres_service['ports']['5432/tcp'] if postgres_service else None

if postgres_service:
    postgres_host = '127.0.0.1'
    postgres_port = postgres_service_port
else:
    postgres_host = None
    postgres_port = None

_postgres_host = Config.value('ZIMAGI_POSTGRES_HOST', None)
if _postgres_host:
    postgres_host = _postgres_host

_postgres_port = Config.value('ZIMAGI_POSTGRES_PORT', None)
if _postgres_port:
    postgres_port = _postgres_port

if not postgres_host or not postgres_port:
    raise ConfigurationError("ZIMAGI_POSTGRES_HOST and ZIMAGI_POSTGRES_PORT environment variables required")

postgres_db = Config.string('ZIMAGI_POSTGRES_DB', 'zimagi')
postgres_user = Config.string('ZIMAGI_POSTGRES_USER', 'postgres')
postgres_password = Config.string('ZIMAGI_POSTGRES_PASSWORD', 'zimagi')
postgres_write_port = Config.value('ZIMAGI_POSTGRES_WRITE_PORT', None)

DATABASES = {
    'default': {
        'ENGINE': 'systems.db.backends.postgresql',
        'NAME': postgres_db,
        'USER': postgres_user,
        'PASSWORD': postgres_password,
        'HOST': postgres_host,
        'PORT': postgres_port,
        'CONN_MAX_AGE': None
    }
}
if postgres_write_port:
    postgres_write_host = Config.value('ZIMAGI_POSTGRES_WRITE_HOST', postgres_host)

    DATABASES['write'] = {
        'ENGINE': 'systems.db.backends.postgresql',
        'NAME': postgres_db,
        'USER': postgres_user,
        'PASSWORD': postgres_password,
        'HOST': postgres_write_host,
        'PORT': postgres_write_port,
        'CONN_MAX_AGE': 1
    }

DISABLE_SERVER_SIDE_CURSORS = True
DB_MAX_CONNECTIONS = Config.integer('ZIMAGI_DB_MAX_CONNECTIONS', 100)
DB_LOCK = threading.Semaphore(DB_MAX_CONNECTIONS)

#
# Redis configurations
#
redis_service = MANAGER.get_service('redis')

if redis_service:
    redis_host = '127.0.0.1'
    redis_port = redis_service['ports']['6379/tcp']
else:
    redis_host = None
    redis_port = None

_redis_host = Config.value('ZIMAGI_REDIS_HOST', None)
if _redis_host:
    redis_host = _redis_host

_redis_port = Config.value('ZIMAGI_REDIS_PORT', None)
if _redis_port:
    redis_port = _redis_port

redis_url = None

if redis_host and redis_port:
    redis_protocol = Config.string('ZIMAGI_REDIS_TYPE', 'redis')
    redis_password = Config.value('ZIMAGI_REDIS_PASSWORD')

    if redis_password:
        redis_url = "{}://:{}@{}:{}".format(
            redis_protocol,
            redis_password,
            redis_host,
            redis_port
        )
    else:
        redis_url = "{}://{}:{}".format(
            redis_protocol,
            redis_host,
            redis_port
        )

#
# Process Management
#
if redis_url:
    REDIS_TASK_URL = "{}/2".format(redis_url)
else:
    REDIS_TASK_URL = None
    QUEUE_COMMANDS = False

#
# Database mutex locking
#
if redis_url:
    REDIS_MUTEX_URL = "{}/3".format(redis_url)
else:
    REDIS_MUTEX_URL = None

MUTEX_TTL_SECONDS = Config.integer('ZIMAGI_MUTEX_TTL_SECONDS', 432000)

#
# Caching configuration
#
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
    }
}

#
# Email configuration
#
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = Config.value('ZIMAGI_EMAIL_HOST', None)
EMAIL_PORT = Config.integer('ZIMAGI_EMAIL_PORT', 25)
EMAIL_HOST_USER = Config.string('ZIMAGI_EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = Config.string('ZIMAGI_EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = Config.boolean('ZIMAGI_EMAIL_USE_TLS', True)
EMAIL_USE_SSL = Config.boolean('ZIMAGI_EMAIL_USE_SSL', False)
EMAIL_SSL_CERTFILE = Config.value('ZIMAGI_EMAIL_SSL_CERTFILE', None)
EMAIL_SSL_KEYFILE = Config.value('ZIMAGI_EMAIL_SSL_KEYFILE', None)
EMAIL_TIMEOUT = Config.value('ZIMAGI_EMAIL_TIMEOUT', None)
EMAIL_SUBJECT_PREFIX = Config.string('ZIMAGI_EMAIL_SUBJECT_PREFIX', '[Zimagi]>')
EMAIL_USE_LOCALTIME = Config.boolean('ZIMAGI_EMAIL_USE_LOCALTIME', True)
