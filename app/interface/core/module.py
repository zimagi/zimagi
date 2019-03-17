from systems.command.base import command_list
from systems.command.factory import resource
from systems.command.types import module


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
            ('provision', ProvisionCommand),
            ('export', ExportCommand),
            ('destroy', DestroyCommand)
        )
