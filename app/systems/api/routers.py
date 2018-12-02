from django.urls import path

from rest_framework import routers

from systems.command import base
from systems.command.types import action
from systems.command import cli
from systems.api import views

import re


class CommandAPIRouter(routers.BaseRouter):

    def get_urls(self):
        utility = cli.AppManagementUtility()
        
        def add_commands(command_tree):
            urls = []

            for name, info in command_tree.items():
                if isinstance(info['cls'], base.AppBaseCommand):
                    if isinstance(info['cls'], action.ActionCommand) and info['cls'].server_enabled():
                        urls.append(path(
                            re.sub(r'\s+', '/', info['name']), 
                            views.ExecuteCommand.as_view(
                                name = info['name'],
                                command = info['cls']
                            )
                        ))
                    urls.extend(add_commands(info['sub']))

            return urls

        return add_commands(utility.fetch_command_tree())
