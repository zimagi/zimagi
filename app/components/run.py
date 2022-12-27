from django.conf import settings

from systems.commands import profile
from systems.commands.profile import ComponentError
from utility.data import get_dict_combinations


class ProfileComponent(profile.BaseProfileComponent):

    def priority(self):
        return 50

    def ensure_module_config(self):
        return True


    def run(self, name, config):
        scopes = self.pop_value('_scopes', config)
        module = self.pop_value('_module', config)
        task = self.pop_value('_task', config)
        command = self.pop_value('_command', config)
        host = self.pop_value('_host', config)
        queue = self.pop_value('_queue', config) if '_queue' in config else settings.QUEUE_COMMANDS
        reverse_status = self.pop_value('_reverse_status', config)

        if not task and not command and not '_config' in config:
            self.command.error("Run {} requires '_task', '_command', or '_config' field".format(name))

        def _execute(data):
            data = self.profile.interpolate_config_value(data)

            if command:
                if host:
                    data['environment_host'] = host
                if settings.QUEUE_COMMANDS:
                    data['push_queue'] = queue
                if reverse_status:
                    data['reverse_status'] = reverse_status

                self.exec(command, **data)

            elif task:
                options = {
                    'module_key': module,
                    'task_key': task,
                    'task_fields': data
                }
                if host:
                    options['environment_host'] = host
                if settings.QUEUE_COMMANDS:
                    options['push_queue'] = queue
                if reverse_status:
                    options['reverse_status'] = reverse_status

                self.exec('task', **options)

            else:
                self.profile.config.set(
                    data.get('_name', name),
                    data.get('_config', None)
                )

        if scopes:
            def _exec_scope(scope):
                _execute(self.interpolate(config, **scope))

            self.run_list(get_dict_combinations(scopes), _exec_scope)
        else:
            _execute(config)
