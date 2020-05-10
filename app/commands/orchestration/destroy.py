from systems.command.types import module


class Command(
    module.ModuleActionCommand
):
    def parse(self):
        self.parse_display_only()
        self.parse_force()
        self.parse_ignore_missing()
        self.parse_profile_components('--components')
        self.parse_module_name()
        self.parse_profile_name()
        self.parse_profile_config_fields(True)

    def confirm(self):
        self.confirmation()

    def exec(self):
        self.module.provider.destroy_profile(
            self.profile_name,
            config = self.profile_config_fields,
            components = self.profile_component_names,
            display_only = self.display_only,
            ignore_missing = self.ignore_missing
        )
