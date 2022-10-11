from systems.commands.index import Command


class Run(Command('run')):

    def exec(self):
        self.module.provider.run_profile(
            self.profile_key,
            config = self.profile_config_fields,
            components = self.profile_components,
            display_only = self.display_only,
            test = self.test,
            ignore_missing = self.ignore_missing
        )
