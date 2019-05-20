from systems.command import profile
from utility.data import get_dict_combinations


class Provisioner(profile.BaseProvisioner):

    def priority(self):
        return 0

    def destroy(self, name, config):
        scopes = self.pop_value('scopes', config)
        module = self.pop_value('module', config)
        task = self.pop_value('task', config)
        command = self.pop_value('command', config)

        if not task and not command:
            self.command.error("Provision {} requires 'task' or 'command' field".format(name))

        def _execute(data):
            if command:
                self.exec(command, **data)
            else:
                self.exec('task',
                    module_name = module,
                    task_name = task,
                    task_fields = data
                )
        if scopes:
            for scope in get_dict_combinations(scopes):
                _execute(self.interpolate(config, **scope))
        else:
            _execute(config)
