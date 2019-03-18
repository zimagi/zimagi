from django.conf import settings

from systems.command.base import command_list
from systems.command.factory import resource
from systems.command.types import module
from systems.command.mixins import db
from utility import docker


class InitCommand(
    module.ModuleActionCommand
):
    def parse(self):
        self.parse_flag('server', '--server', 'initialize server runtime modules')

    def exec(self):
        self._module.ensure(self, True, self.options.get('server', False))


class InstallCommand(
    module.ModuleActionCommand
):
    def parse(self):
        self.parse_flag('server', '--server', 'install module requirements on server runtime')

    def exec(self):
        settings.LOADER.install_requirements()

        if not self.options.get('server', False):
            env = self.get_env()
            cid = docker.Docker.container_id
            image = docker.Docker.generate_image(env.base_image)

            docker.Docker.create_image(cid, image)
            env.runtime_image = image
            env.save()

        self.success("Successfully installed module requirements")


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


class ExportCommand(
    module.ModuleActionCommand
):
    def display_header(self):
        return False

    def parse(self):
        self.parse_profile_components(True)

    def exec(self):
        self.options.add('module_name', 'core')
        self.module.provider.export_profile(
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

    def get_command_name(self):
        return 'module'

    def get_subcommands(self):
        base_name = self.get_command_name()
        return command_list(
            resource.ResourceCommandSet(
                module.ModuleActionCommand, base_name,
                provider_name = base_name
            ),
            ('init', InitCommand),
            ('install', InstallCommand),
            ('sync', SyncCommand),
            ('provision', ProvisionCommand),
            ('export', ExportCommand),
            ('destroy', DestroyCommand)
        )
