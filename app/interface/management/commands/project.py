from systems.command.base import command_list
from systems.command import types, mixins, factory


class ProvisionCommand(
    types.ProjectActionCommand
):
    def parse(self):
        self.parse_profile_components('--components')
        self.parse_project_name()
        self.parse_profile_name()

    def exec(self):
        self.project.provider.provision_profile(
            self.profile_name,
            self.profile_component_names
        )


class ExportCommand(
    types.ProjectActionCommand
):
    def parse(self):
        self.parse_profile_components(True)

    def exec(self):
        self.options.add('project_name', 'core')
        self.project.provider.export_profile(
            self.profile_component_names
        )


class DestroyCommand(
    types.ProjectActionCommand
):
    def parse(self):
        self.parse_force()
        self.parse_profile_components('--components')
        self.parse_project_name()
        self.parse_profile_name()

    def confirm(self):
        self.confirmation()

    def exec(self):
        self.project.provider.destroy_profile(
            self.profile_name,
            self.profile_component_names
        )


class Command(types.ProjectRouterCommand):

    def get_command_name(self):
        return 'project'

    def get_subcommands(self):
        base_name = self.get_command_name()
        return command_list(
            factory.ResourceCommandSet(
                types.ProjectActionCommand, base_name,
                provider_name = base_name
            ),
            ('provision', ProvisionCommand),
            ('export', ExportCommand),
            ('destroy', DestroyCommand)
        )
