from systems.command import types, mixins


class ListCommand(
    mixins.op.ListMixin,
    types.UserActionCommand
):
    def exec(self):
        def process(op, info, key_index):
            if op == 'label':
                info.append('Groups')
            else:
                user = self.get_instance(self._user, info[key_index])
                info.append("\n".join(user.groups.values_list('name', flat = True)))

        self.exec_processed_list(self._user, process,
            ('id', 'ID'), 
            ('username', 'Username'),
            ('first_name', 'First name'),
            ('last_name', 'Last name'),
            ('email', 'Email')
        )
