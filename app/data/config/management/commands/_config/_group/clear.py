from systems.command import types, mixins


class ClearCommand(
    mixins.op.RemoveMixin,
    types.ConfigGroupActionCommand
):
    def parse(self):
        self.parse_config_groups(True)

    def confirm(self):
        self.confirmation()       

    def exec(self):
        def remove_groups(config, state):
            self.exec_rm_related(
                self._config_group, 
                config, 'groups', 
                self.config_group_names
            )    
        self.run_list(self.get_instances(self._config), remove_groups)

        for group in self.config_group_names:
            self.exec_rm(self._config_group, group)
