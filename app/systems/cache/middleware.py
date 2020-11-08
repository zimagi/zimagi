from django.conf import settings
from django.core.cache import caches
from django.utils.cache import (
    get_cache_key, get_max_age, has_vary_header, learn_cache_key,
    patch_response_headers,
)
from django.utils.deprecation import MiddlewareMixin

from systems.models.index import Model


class UpdateCacheMiddleware(MiddlewareMixin):

    def __init__(self, get_response):
        super().__init__(get_response)

        self.cache_timeout = settings.CACHE_MIDDLEWARE_SECONDS
        self.key_prefix = settings.CACHE_MIDDLEWARE_KEY_PREFIX
        self.cache_alias = settings.CACHE_MIDDLEWARE_ALIAS
        self.cache = caches[self.cache_alias]


    def process_response(self, request, response):
        if request.path != '/status':
            cache_entry = Model('cache').facade.get_or_create(request.build_absolute_uri())
            cache_entry.requests += 1
            cache_entry.save()

        if not (hasattr(request, '_cache_update_cache') and request._cache_update_cache):
            return response

        response['Object-Cache'] = 'MISS'

        if response.streaming or response.status_code not in (200, 304):
            return response

        if not request.COOKIES and response.cookies and has_vary_header(response, 'Cookie'):
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
            cache_key = learn_cache_key(request, response, timeout, self.key_prefix, cache = self.cache)
            if hasattr(response, 'render') and callable(response.render):
                response.add_post_render_callback(
                    lambda r: self.cache.set(cache_key, r, timeout)
                )
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

        if request.GET.get('refresh', False):
            request._cache_update_cache = True
            return None

        cache_key = get_cache_key(request, self.key_prefix, 'GET', cache = self.cache)
        if cache_key is None:
            request._cache_update_cache = True
            return None

        response = self.cache.get(cache_key)
        if response is None and request.method == 'HEAD':
            cache_key = get_cache_key(request, self.key_prefix, 'HEAD', cache = self.cache)
            response = self.cache.get(cache_key)

        if response is None:
            request._cache_update_cache = True
            return None

        request._cache_update_cache = False
        response['Object-Cache'] = 'HIT'
        return response
