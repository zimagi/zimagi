from systems.command import profile
from utility.data import get_dict_combinations


class ProfileComponent(profile.BaseProfileComponent):

    def priority(self):
        return 0

    def destroy(self, name, config):
        scopes = self.pop_value('scopes', config)
        module = self.pop_value('module', config)
        task = self.pop_value('task', config)
        command = self.pop_value('command', config)
        host = self.pop_value('host', config)

        if not task and not command:
            self.command.error("Destroy {} requires 'task' or 'command' field".format(name))

        def _execute(data):
            if command:
                data['local'] = self.command.local

                if host:
                    data['environment_host'] = host

                self.exec(command, **data)
            else:
                options = {
                    'module_name': module,
                    'task_name': task,
                    'task_fields': data,
                    'local': self.command.local

                }
                if host:
                    options['environment_host'] = host

                self.exec('task', **options)
        if scopes:
            for scope in get_dict_combinations(scopes):
                _execute(self.interpolate(config, **scope))
        else:
            _execute(config)
