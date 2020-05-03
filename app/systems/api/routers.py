from django.conf import settings
from django.conf.urls import url
from django.urls import path

from rest_framework import routers

from systems.command import base
from systems.command.types import action
from systems.command import registry
from systems.api import views
from utility.runtime import Runtime

import re


class CommandAPIRouter(routers.BaseRouter):

    def get_urls(self):
        def add_commands(command_tree):
            urls = []

            for name, info in command_tree.items():
                if isinstance(info['instance'], base.AppBaseCommand):

                    if settings.API_EXEC:
                        info['instance'].parse_base()

                    if isinstance(info['instance'], action.ActionCommand) and info['instance'].server_enabled():
                        urls.append(path(
                            re.sub(r'\s+', '/', info['name']),
                            views.Command.as_view(
                                name = info['name'],
                                command = info['instance']
                            )
                        ))
                    urls.extend(add_commands(info['sub']))

            return urls

        return add_commands(
            registry.CommandRegistry().fetch_command_tree()
        )


class DataAPIRouter(routers.SimpleRouter):

    routes = [
        # List route
        routers.Route(
            url = r'^{prefix}{trailing_slash}$',
            mapping = {
                'get': 'list',
                'post': 'create'
            },
            name = '{basename}-list',
            detail = False,
            initkwargs = {
                'suffix': 'List'
            }
        ),
        routers.DynamicRoute(
            url = r'^{prefix}/{url_path}{trailing_slash}$',
            name = '{basename}-{url_name}',
            detail = False,
            initkwargs = {}
        ),
        # Detail route
        routers.Route(
            url = r'^{prefix}/{lookup}{trailing_slash}$',
            mapping = {
                'get': 'retrieve',
                'put': 'update',
                'patch': 'partial_update',
                'delete': 'destroy'
            },
            name = '{basename}-detail',
            detail = True,
            initkwargs = {
                'suffix': 'Instance'
            }
        ),
        routers.DynamicRoute(
            url = r'^{prefix}/{lookup}/{url_path}{trailing_slash}$',
            name = '{basename}-{url_name}',
            detail = True,
            initkwargs = {}
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


    def get_urls(self):
        urls = []

        for name, facade in settings.MANAGER.get_facade_index().items():
            if getattr(facade, 'viewset', None):
                self.register(name, facade.viewset)

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