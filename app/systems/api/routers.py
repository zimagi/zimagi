from functools import lru_cache

from django.conf import settings
from django.conf.urls import url
from django.urls import path

from rest_framework import routers

from systems.commands import action, router
from systems.api import views
from utility.runtime import Runtime

import re


class CommandAPIRouter(routers.BaseRouter):

    def get_urls(self):
        urls = []

        def add_commands(command):
            for subcommand in command.get_subcommands():
                if isinstance(subcommand, router.RouterCommand):
                    add_commands(subcommand)

                elif isinstance(subcommand, action.ActionCommand) and subcommand.server_enabled():
                    if settings.API_EXEC:
                        subcommand.parse_base()

                    name = subcommand.get_full_name()
                    urls.append(path(
                        re.sub(r'\s+', '/', name),
                        views.Command.as_view(
                            name = name,
                            command = subcommand
                        )
                    ))

        add_commands(settings.MANAGER.index.command_tree)
        return urls


class DataAPIRouter(routers.SimpleRouter):

    routes = [
        # List route
        routers.Route(
            url = r'^{prefix}{trailing_slash}$',
            mapping = {
                'get': 'list'
            },
            name = '{basename}-list',
            detail = False,
            initkwargs = {
                'suffix': 'List'
            }
        ),
        # Meta route
        routers.Route(
            url = r'^{prefix}/meta{trailing_slash}$',
            mapping = {
                'get': 'meta'
            },
            name = '{basename}-meta',
            detail = False,
            initkwargs = {
                'suffix': 'Meta'
            }
        ),
        # CSV route
        routers.Route(
            url = r'^{prefix}/csv{trailing_slash}$',
            mapping = {
                'get': 'csv'
            },
            name = '{basename}-csv',
            detail = False,
            initkwargs = {
                'suffix': 'CSV'
            }
        ),
        # JSON route
        routers.Route(
            url = r'^{prefix}/json{trailing_slash}$',
            mapping = {
                'get': 'json'
            },
            name = '{basename}-csv',
            detail = False,
            initkwargs = {
                'suffix': 'JSON'
            }
        ),
        # Values route
        routers.Route(
            url = r'^{prefix}/values/{field_lookup}{trailing_slash}$',
            mapping = {
                'get': 'values'
            },
            name = '{basename}-values',
            detail = False,
            initkwargs = {
                'suffix': 'Values'
            }
        ),
        # Count route
        routers.Route(
            url = r'^{prefix}/count/{field_lookup}{trailing_slash}$',
            mapping = {
                'get': 'count'
            },
            name = '{basename}-count',
            detail = False,
            initkwargs = {
                'suffix': 'Count'
            }
        ),
        # Detail route
        routers.Route(
            url = r'^{prefix}/{lookup}{trailing_slash}$',
            mapping = {
                'get': 'retrieve'
            },
            name = '{basename}-detail',
            detail = True,
            initkwargs = {
                'suffix': 'Instance'
            }
        )
    ]


    def __init__(self):
        self.trailing_slash = '/?'
        super().__init__()


    def get_field_lookup_regex(self, viewset, lookup_prefix=''):
        base_regex = '(?P<{lookup_prefix}field_lookup>{lookup_value})'
        lookup_value = getattr(viewset, 'lookup_value_regex', '[^/.]+')

        return base_regex.format(
            lookup_prefix = lookup_prefix,
            lookup_value = lookup_value
        )


    @lru_cache(maxsize = None)
    def get_urls(self):
        urls = []

        for name, facade in settings.MANAGER.index.get_facade_index().items():
            data_spec = settings.MANAGER.get_spec("data.{}".format(name))
            if data_spec.get('api', True):
                self.register(facade.name, facade.get_viewset())

        for prefix, viewset, basename in self.registry:
            lookup = self.get_lookup_regex(viewset)
            field_lookup = self.get_field_lookup_regex(viewset)
            routes = self.get_routes(viewset)

            for route in routes:
                mapping = self.get_method_map(viewset, route.mapping)
                if not mapping:
                    continue

                regex = route.url.format(
                    prefix = prefix,
                    lookup = lookup,
                    field_lookup = field_lookup,
                    trailing_slash = self.trailing_slash
                )

                if not prefix and regex[:2] == '^/':
                    regex = '^' + regex[2:]

                initkwargs = route.initkwargs.copy()
                initkwargs.update({
                    'basename': basename,
                    'detail': route.detail
                })

                view = viewset.as_view(mapping, **initkwargs)
                name = route.name.format(basename = basename)
                urls.append(url(regex, view, name = name))

        return urls
