from systems.command import types, mixins


class ClearCommand(
    types.ConfigActionCommand
):
    def parse(self):
        self.parse_force()
    
    def confirm(self):
        self.confirmation()       

    def exec(self):
        def remove_config(config, state):
            self.exec_local('config rm', {
                'config_name': config.name,
                'force': self.force
            })
        self.run_list(self.configs, remove_config)
