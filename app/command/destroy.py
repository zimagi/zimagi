from systems.command.index import Command


class Action(Command('destroy')):

    def exec(self):
        self.module.provider.destroy_profile(
            self.profile_name,
            config = self.profile_config_fields,
            components = self.profile_component_names,
            display_only = self.display_only,
            ignore_missing = self.ignore_missing
        )
