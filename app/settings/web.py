"""
Application settings definition

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""
from .full import *
from .config import Config


#-------------------------------------------------------------------------------
# Core settings

#
# Caching configuration
#
CACHES['page'] = {
    'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
}

if redis_url and not Config.boolean('ZIMAGI_DISABLE_PAGE_CACHE', False):
    CACHES['page'] = {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "{}/1".format(redis_url),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "IGNORE_EXCEPTIONS": True,
            "PARSER_CLASS": "redis.connection.HiredisParser"
        }
    }

CACHE_MIDDLEWARE_ALIAS = 'page'
CACHE_MIDDLEWARE_KEY_PREFIX = ''
CACHE_MIDDLEWARE_SECONDS = Config.integer('ZIMAGI_PAGE_CACHE_SECONDS', 86400) # 1 Day

CACHE_PARAM = 'refresh'

#-------------------------------------------------------------------------------
# Django Addons

#
# API configuration
#
ALLOWED_HOSTS = Config.list('ZIMAGI_ALLOWED_HOSTS', ['*'])

CORS_ALLOWED_ORIGINS = Config.list('ZIMAGI_CORS_ALLOWED_ORIGINS', [])
CORS_ALLOWED_ORIGIN_REGEXES = Config.list('ZIMAGI_CORS_ALLOWED_ORIGIN_REGEXES', [])
CORS_ALLOW_ALL_ORIGINS = Config.boolean('ZIMAGI_CORS_ALLOW_ALL_ORIGINS', True)

CORS_ALLOW_METHODS = [
    'GET',
    'POST',
    'PUT',
    'DELETE'
]

SECURE_CROSS_ORIGIN_OPENER_POLICY = Config.string('ZIMAGI_SECURE_CROSS_ORIGIN_OPENER_POLICY', 'unsafe-none')
SECURE_REFERRER_POLICY = Config.string('ZIMAGI_SECURE_REFERRER_POLICY', 'no-referrer')
