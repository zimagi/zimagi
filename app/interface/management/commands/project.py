from systems.command.base import command_list
from systems.command import types, mixins, factory


class ProvisionCommand(
    types.ProjectActionCommand
):
    def parse(self):
        self.parse_profile_components('--components')
        self.parse_project_name()
        self.parse_profile_name()
        self.parse_profile_fields(True)

    def exec(self):
        self.project.provider.provision_profile(
            self.profile_name,
            self.profile_component_names, 
            self.profile_fields
        )


class ExportCommand(
    types.ProjectActionCommand
):
    def parse(self):
        self.parse_profile_components('--components')
        self.parse_project_name()
        self.parse_profile_name()

    def exec(self):
        self.project.provider.export_profile(
            self.profile_name,
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

    def exec(self):
        self.project.provider.destroy_profile(
            self.profile_name,
            self.profile_component_names
        )


class Command(types.ProjectRouterCommand):

    def get_command_name(self):
        return 'project'

    def get_subcommands(self):
        return command_list(
            factory.ResourceCommands(
                types.ProjectActionCommand, 'project',
                relations = {
                    'groups': ('group_names', '--groups')
                }
            ),
            ('provision', ProvisionCommand),
            ('export', ExportCommand),
            ('destroy', DestroyCommand)
        )
