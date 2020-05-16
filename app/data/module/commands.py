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


class InitCommand(
    ModuleActionCommand
):
    def exec(self):
        self._module.ensure(self, True)


class InstallCommand(
    ModuleActionCommand
):
    def exec(self):
        self.info("Installing module requirements...")
        self.manager.install_scripts(self, self.verbosity == 3)
        self.manager.install_requirements(self, self.verbosity == 3)

        if settings.CLI_EXEC:
            env = self.get_env()
            cid = self.manager.container_id
            image = self.manager.generate_image_name(env.base_image)

            self.manager.create_image(cid, image)
            env.runtime_image = image
            env.save()

        self.success("Successfully installed module requirements")


class ResetCommand(
    ModuleActionCommand
):
    def exec(self):
        env = self.get_env()
        env.runtime_image = None
        env.save()
        self.set_state('module_ensure', True)
        self.success("Successfully reset module runtime")


class SyncCommand(
    db.DatabaseMixin,
    ModuleActionCommand
):
    def exec(self):
        self.silent_data('modules', self.db.save('module', encrypted = False))

    def postprocess(self, result):
        self.db.load(result.get_named_data('modules'), encrypted = False)
        for module in self.get_instances(self._module):
            module.provider.update()

        self.exec_local('module install')
        self.success('Modules successfully synced from remote environment')


class Command(ModuleRouterCommand):

    def get_subcommands(self):
        return command_set(
            resource.ResourceCommandSet(
                ModuleActionCommand, self.name,
                provider_name = self.name
            ),
            ('init', InitCommand),
            ('install', InstallCommand),
            ('reset', ResetCommand),
            ('sync', SyncCommand)
        )
