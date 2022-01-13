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

    def destroy(self, name, config):
        scopes = self.pop_value('_scopes', config)
        module = self.pop_value('_module', config)
        task = self.pop_value('_task', config)
        command = self.pop_value('_command', config)
        host = self.pop_value('_host', config)

        if not task and not command and not self.get_value('_config', config):
            self.command.error("Destroy {} requires '_task', '_command', or '_config' field".format(name))

        def _execute(data):
            if command:
                options = {}
                if host:
                    options['environment_host'] = host

                for key, value in data.items():
                    key = self.command.options.interpolate(key)
                    options[key] = value

                self.exec(command, **options)
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
                ConfigParser.runtime_variables[name] = self.command.options.interpolate(data.get('_config', None))

        if scopes:
            for scope in get_dict_combinations(scopes):
                _execute(self.interpolate(config, **scope))
        else:
            _execute(config)
