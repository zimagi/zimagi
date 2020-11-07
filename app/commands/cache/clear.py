from django.conf import settings
from django.core.cache import caches

from systems.commands.index import Command


class Clear(Command('cache.clear')):

    def exec(self):
        caches[settings.CACHE_MIDDLEWARE_ALIAS].clear()
        caches[settings.CACHE_MIDDLEWARE_ALIAS].close()
