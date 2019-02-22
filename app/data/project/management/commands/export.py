from django.conf import settings

from systems.command import types, mixins


class Command(
    mixins.data.NetworkMixin,
    types.EnvironmentActionCommand
):
    def get_command_name(self):
        return 'export'

    def server_enabled(self):
        return True
    
    def parse(self):
        self.parse_profile_components('--components')
        self.parse_project_name()
        self.parse_profile_name()

    def exec(self):
        self.project.provider.export_profile(
            self.profile_name,
            self.profile_component_names
        )
