from systems.commands import profile
from plugins.parser.config import Provider as ConfigParser
from utility.data import get_dict_combinations


class ProfileComponent(profile.BaseProfileComponent):

    def priority(self):
        return 0

    def ensure_module_config(self):
        return True


    def skip_run(self):
        return True

    def skip_describe(self):
        return True


    def destroy(self, name, config):
        scopes = self.pop_value('scopes', config)
        module = self.pop_value('module', config)
        task = self.pop_value('task', config)
        command = self.pop_value('command', config)
        host = self.pop_value('host', config)

        if not task and not command and not self.get_value('config', config):
            self.command.error("Destroy {} requires 'task', 'command', or 'config' field".format(name))

        def _execute(data):
            if command:
                if host:
                    data['environment_host'] = host

                self.exec(command, **data)
            elif task:
                options = {
                    'module_name': module,
                    'task_name': task,
                    'task_fields': data
                }
                if host:
                    options['environment_host'] = host

                self.exec('task', **options)
            else:
                ConfigParser.runtime_variables[data['config']] = self.command.options.interpolate(data.get('value', None))

        if scopes:
            for scope in get_dict_combinations(scopes):
                _execute(self.interpolate(config, **scope))
        else:
            _execute(config)
