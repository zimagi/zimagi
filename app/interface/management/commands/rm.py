from systems.command import types, mixins


class Command(
    mixins.op.RemoveMixin,
    types.EnvironmentActionCommand
):
    def get_command_name(self):
        return 'rm'

    def parse(self):
        self.parse_force()

    def confirm(self):
        self.confirmation()       

    def exec(self):
        env = self.get_env()

        def process(type, state):
            self.exec_local("{} clear".format(type), {
                'force': self.force
            })
        self.run_list(('federation', 'network', 'project', 'config'), process)
        
        self.exec_rm(self._env, env.name, display_warning = False)
        self.delete_env()
