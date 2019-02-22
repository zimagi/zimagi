from systems.command import types, mixins


class AddCommand(
    mixins.op.AddMixin,
    types.ConfigGroupActionCommand
):
    def parse(self):
        self.parse_config_reference()
        self.parse_config_groups(None)

    def exec(self):
        def add_groups(config, state):
            self.exec_add_related(
                self._config_group, 
                config, 'groups', 
                self.config_group_names
            )
        self.run_list(self.configs, add_groups)
