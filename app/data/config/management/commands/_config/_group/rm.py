from systems.command import types, mixins


class RemoveCommand(
    mixins.op.RemoveMixin,
    types.ConfigGroupActionCommand
):
    def parse(self):
        self.parse_config_reference()
        self.parse_config_groups(None)

    def confirm(self):
        self.confirmation()       

    def exec(self):
        def remove_groups(config, state):
            self.exec_rm_related(
                self._config_group, 
                config, 'groups', 
                self.config_group_names
            )
        self.run_list(self.configs, remove_groups)
