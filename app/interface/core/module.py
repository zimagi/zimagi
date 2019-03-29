from django.conf import settings

from systems.command.base import command_list
from systems.command.factory import resource
from systems.command.types import module
from systems.command.mixins import db


class InitCommand(
    module.ModuleActionCommand
):
    def exec(self):
        self._module.ensure(self, True)


class InstallCommand(
    module.ModuleActionCommand
):
    def exec(self):
        self.info("Installing module requirements...")
        self.manager.install_scripts(self, self.verbosity == 3)
        self.manager.install_requirements(self, self.verbosity == 3)

        if not settings.API_INIT and not settings.API_EXEC:
            env = self.get_env()
            cid = self.manager.container_id
            image = self.manager.generate_image_name(env.base_image)

            self.manager.create_image(cid, image)
            env.runtime_image = image
            env.save()

        self.success("Successfully installed module requirements")


class ResetCommand(
    module.ModuleActionCommand
):
    def exec(self):
        env = self.get_env()
        env.runtime_image = None
        env.save()
        self.success("Successfully reset module runtime")


class SyncCommand(
    db.DatabaseMixin,
    module.ModuleActionCommand
):
    def exec(self):
        self.silent_data('modules', self.db.save('module', encrypted = False))

    def postprocess(self, result):
        self.db.load(result.get_named_data('modules'), encrypted = False)
        for module in self.get_instances(self._module):
            module.provider.update()

        self.exec_local('module install')
        self.success('Modules successfully synced from remote environment')


class ProvisionCommand(
    module.ModuleActionCommand
):
    def parse(self):
        self.parse_profile_components('--components')
        self.parse_module_name()
        self.parse_profile_name()

    def exec(self):
        self.module.provider.provision_profile(
            self.profile_name,
            self.profile_component_names
        )


class DestroyCommand(
    module.ModuleActionCommand
):
    def parse(self):
        self.parse_force()
        self.parse_profile_components('--components')
        self.parse_module_name()
        self.parse_profile_name()

    def confirm(self):
        self.confirmation()

    def exec(self):
        self.module.provider.destroy_profile(
            self.profile_name,
            self.profile_component_names
        )


class Command(module.ModuleRouterCommand):

    def get_subcommands(self):
        return command_list(
            resource.ResourceCommandSet(
                module.ModuleActionCommand, self.name,
                provider_name = self.name
            ),
            ('init', InitCommand),
            ('install', InstallCommand),
            ('reset', ResetCommand),
            ('sync', SyncCommand),
            ('provision', ProvisionCommand),
            ('destroy', DestroyCommand)
        )
