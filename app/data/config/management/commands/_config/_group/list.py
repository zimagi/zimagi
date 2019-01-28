from settings import Roles
from systems.command import types, mixins


class ListCommand(
    mixins.op.ListMixin,
    types.ConfigGroupActionCommand
):
    def groups_allowed(self):
        return False # Configuration access model

    def get_description(self, overview):
        if overview:
            return """list environment groups for configuration

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """list environment groups for configuration
                      
Etiam mattis iaculis felis eu pharetra. Nulla facilisi. 
Duis placerat pulvinar urna et elementum. Mauris enim risus, 
mattis vel risus quis, imperdiet convallis felis. Donec iaculis 
tristique diam eget rutrum.

Etiam sit amet mollis lacus. Nulla pretium, neque id porta feugiat, 
erat sapien sollicitudin tellus, vel fermentum quam purus non sem. 
Mauris venenatis eleifend nulla, ac facilisis nulla efficitur sed. 
Etiam a ipsum odio. Curabitur magna mi, ornare sit amet nulla at, 
scelerisque tristique leo. Curabitur ut faucibus leo, non tincidunt 
velit. Aenean sit amet consequat mauris.
"""
    def parse(self):
        self.parse_config_groups(True)

    def exec(self):
        def process(op, info, key_index):
            if op == 'label':
                info.extend(['Name', 'Value', 'User', 'Description'])
            else:
                config_names = []
                config_values = []
                config_users = []
                config_descriptions = []

                for config in self.get_instances(self._config, groups = info[key_index]):
                    config_names.append(config.name)
                    config_values.append(config.value)
                    config_users.append(config.user)
                    config_descriptions.append(config.description)
                    
                info.append("\n".join(config_names))
                info.append("\n".join(config_values))
                info.append("\n".join(config_users))
                info.append("\n".join(config_descriptions))

        if self.config_group_names:
            self.exec_processed_sectioned_list(
                self._config_group, process, 
                ('name', 'Group'),
                name__in = self.config_group_names
            )
        else:
            self.exec_processed_sectioned_list(self._config_group, process, ('name', 'Group'))
