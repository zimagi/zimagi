from systems.command import types, mixins


class ListCommand(
    mixins.op.ListMixin,
    types.ConfigActionCommand
):
    def groups_allowed(self):
        return False # Configuration model access

    def exec(self):
        def process(op, info, key_index):
            if op == 'label':
                info.extend(['Groups'])
            else:
                config = self.get_instance(self._config, info[key_index])
                info.append("\n".join(config.groups.values_list('name', flat = True)))

        self.exec_processed_list(self._config, process,
            ('name', 'Name'),
            ('_value', 'Value'),
            ('user', 'User')
        )
