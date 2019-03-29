from systems.command.types import module


class Command(
    module.ModuleActionCommand
):
    def display_header(self):
        return False

    def parse(self):
        self.parse_profile_components(True)

    def exec(self):
        self.options.add('module_name', 'core')
        self.module.provider.export_profile(
            self.profile_component_names
        )
