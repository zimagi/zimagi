from systems.commands.index import Command


class Destroy(Command('destroy')):

    def exec(self):
        self.module.provider.destroy_profile(
            self.profile_name,
            config = self.profile_config_fields,
            components = self.profile_components,
            display_only = self.display_only,
            ignore_missing = self.ignore_missing
        )
