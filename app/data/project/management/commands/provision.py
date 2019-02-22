from django.conf import settings

from systems.command import types, mixins


class Command(
    mixins.data.NetworkMixin,
    types.EnvironmentActionCommand
):
    def get_command_name(self):
        return 'provision'

    def server_enabled(self):
        return True
    
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
