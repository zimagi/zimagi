from django.conf import settings
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
