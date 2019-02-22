from settings import Roles
from systems.command import types, mixins


class ListCommand(
    mixins.op.ListMixin,
    types.ConfigGroupActionCommand
):
    def groups_allowed(self):
        return False # Configuration access model

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
