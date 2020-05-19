from django.conf import settings

from settings.roles import Roles
from base.command.base import command_set
from base.command.router import RouterCommand
from base.command.action import ActionCommand
from mixins.command import db
from systems.command.factory import resource

import time


class ModuleRouterCommand(RouterCommand):

    def get_priority(self):
        return 70


class ModuleActionCommand(ActionCommand):

    def groups_allowed(self):
        return [
            Roles.admin,
            Roles.module_admin
        ]

    def server_enabled(self):
        return True

    def get_priority(self):
        return 70


class Command(ModuleRouterCommand):

    def get_subcommands(self):
        return command_set(
            resource.ResourceCommandSet(
                ModuleActionCommand, self.name,
                provider_name = self.name
            )
        )
