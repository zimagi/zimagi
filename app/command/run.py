from settings.roles import Roles
from systems.command.action import ActionCommand


class Command(ActionCommand):

    def groups_allowed(self):
        return [
            Roles.admin,
            Roles.module_admin
        ]

    def server_enabled(self):
        return True

    def get_priority(self):
        return 70

    def parse(self):
        self.parse_display_only()
        self.parse_plan()
        self.parse_ignore_missing()
        self.parse_profile_components('--components')
        self.parse_module_name()
        self.parse_profile_name()
        self.parse_profile_config_fields(True)

    def exec(self):
        self.module.provider.run_profile(
            self.profile_name,
            config = self.profile_config_fields,
            components = self.profile_component_names,
            display_only = self.display_only,
            plan = self.plan,
            ignore_missing = self.ignore_missing
        )
