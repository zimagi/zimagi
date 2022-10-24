from django.conf import settings
from django.core.cache import caches
from django.utils.crypto import md5
from django.utils.cache import (
    get_max_age,
    patch_response_headers
)
from django.utils.deprecation import MiddlewareMixin

from systems.models.index import Model
from systems.models.base import run_transaction


def get_cache_key(request, key_prefix):
    auth = request.headers.get('Authorization')
    user = md5(
        auth.encode() if auth else settings.ANONYMOUS_USER.encode(),
        usedforsecurity = False
    )
    url = md5(
        request.build_absolute_uri().encode('ascii'),
        usedforsecurity = False
    )
    return "page.{}.{}.{}.{}".format(
        key_prefix if key_prefix else settings.CACHE_MIDDLEWARE_KEY_PREFIX,
        request.method,
        url.hexdigest(),
        user.hexdigest()
    )


class UpdateCacheMiddleware(MiddlewareMixin):

    def __init__(self, get_response):
        super().__init__(get_response)

        self.cache_timeout = settings.CACHE_MIDDLEWARE_SECONDS
        self.key_prefix = settings.CACHE_MIDDLEWARE_KEY_PREFIX
        self.cache_alias = settings.CACHE_MIDDLEWARE_ALIAS
        self.cache = caches[self.cache_alias]


    def process_response(self, request, response):
        if request.path != '/status':
            request_id = "{}:{}".format(request.method, request.build_absolute_uri())
            cache_facade = Model('cache').facade

            def cache_transaction():
                cache_entry = cache_facade.get_or_create(request_id)
                cache_entry.requests += 1
                cache_entry.save()

            run_transaction(cache_facade, request_id, cache_transaction)

        if not (hasattr(request, '_cache_update_cache') and request._cache_update_cache):
            return response

        response['Object-Cache'] = 'MISS'

        if response.streaming or response.status_code not in (200, 304):
            return response

        if 'private' in response.get('Cache-Control', ()):
            return response

        timeout = get_max_age(response)
        if timeout is None:
            timeout = self.cache_timeout
        elif timeout == 0:
            return response

        patch_response_headers(response, timeout)

        if timeout and response.status_code == 200:
            cache_key = get_cache_key(request, self.key_prefix)
            if hasattr(response, 'render') and callable(response.render):
                def callback(r):
                    self.cache.set(cache_key, r, timeout)

                response.add_post_render_callback(callback)
            else:
                self.cache.set(cache_key, response, timeout)

        return response


class FetchCacheMiddleware(MiddlewareMixin):

    def __init__(self, get_response):
        super().__init__(get_response)

        self.key_prefix = settings.CACHE_MIDDLEWARE_KEY_PREFIX
        self.cache_alias = settings.CACHE_MIDDLEWARE_ALIAS
        self.cache = caches[self.cache_alias]


    def process_request(self, request):
        if request.method not in ('GET', 'HEAD') or request.path == '/status':
            request._cache_update_cache = False
            return None

        if request.GET.get(settings.CACHE_PARAM, False):
            request._cache_update_cache = True
            return None

        cache_key = get_cache_key(request, self.key_prefix)
        response = self.cache.get(cache_key)
        if response is None:
            request._cache_update_cache = True
            return None

        request._cache_update_cache = False
        response['Object-Cache'] = 'HIT'
        return response
