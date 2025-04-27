import re

from django.conf import settings
from django.urls import path
from rest_framework import routers
from systems.commands import exec, router

from . import views


class CommandAPIRouter(routers.BaseRouter):
    def get_urls(self):
        urls = []

        def add_commands(command):
            for subcommand in command.get_subcommands():
                if isinstance(subcommand, router.RouterCommand):
                    add_commands(subcommand)

                elif isinstance(subcommand, exec.ExecCommand) and subcommand.server_enabled():
                    if settings.WSGI_EXEC:
                        subcommand.parse_base()

                    name = subcommand.get_full_name()
                    urls.append(path(re.sub(r"\s+", "/", name), views.Command.as_view(name=name, command=subcommand)))

        add_commands(settings.MANAGER.index.command_tree)
        return urls
