from systems.commands import profile
from utility.data import get_dict_combinations


class ProfileComponent(profile.BaseProfileComponent):

    def priority(self):
        return 100

    def ensure_module_config(self):
        return True


    def skip_destroy(self):
        return True

    def run(self, name, config):
        scopes = self.pop_value('_scopes', config)
        module = self.pop_value('_module', config)
        task = self.pop_value('_task', config)
        command = self.pop_value('_command', config)
        host = self.pop_value('_host', config)

        if not task and not command and not '_config' in config:
            self.command.error("Run {} requires '_task', '_command', or '_config' field".format(name))

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
                self.profile.config.set(
                    data.get('_name', name),
                    data.get('_config', None)
                )
        if scopes:
            for scope in get_dict_combinations(scopes):
                _execute(self.interpolate(config, **scope))
        else:
            _execute(config)
