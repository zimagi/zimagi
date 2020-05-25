from systems.command.index import Command


class Action(Command('export')):

    def exec(self):
        self.options.add('module_name', 'core')
        self.module.provider.export_profile(
            self.profile_component_names
        )
