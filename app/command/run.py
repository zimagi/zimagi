from systems.command.index import Command


class Action(Command('run')):

    def exec(self):
        self.module.provider.run_profile(
            self.profile_name,
            config = self.profile_config_fields,
            components = self.profile_component_names,
            display_only = self.display_only,
            plan = self.plan,
            ignore_missing = self.ignore_missing
        )
