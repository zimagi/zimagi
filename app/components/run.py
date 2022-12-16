from django.conf import settings

from systems.commands import profile
from systems.commands.profile import ComponentError
from utility.data import get_dict_combinations

import threading


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

        thread_lock = threading.Lock()
        log_keys = []

        if not task and not command and not '_config' in config:
            self.command.error("Run {} requires '_task', '_command', or '_config' field".format(name))

        def _execute(data):
            if command:
                if host:
                    data['environment_host'] = host
                if settings.QUEUE_COMMANDS:
                    data['push_queue'] = queue

                keys = self.exec(command, **data)
                with thread_lock:
                    log_keys.append(keys)

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

                keys = self.exec('task', **options)
                with thread_lock:
                    log_keys.append(keys)

            else:
                with thread_lock:
                    self.profile.config.set(
                        data.get('_name', name),
                        data.get('_config', None)
                    )

        if scopes:
            def _exec_scope(scope):
                _execute(self.interpolate(config, **scope))

            combo_list = get_dict_combinations(scopes)
            parallel_options = {}
            if queue:
                parallel_options['thread_count'] = len(combo_list)

            results = self.command.run_list(combo_list, _exec_scope, **parallel_options)
            if results.errors:
                raise ComponentError("\n\n".join(results.errors))
        else:
            _execute(config)

        return log_keys if queue else []
