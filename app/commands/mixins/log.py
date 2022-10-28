from systems.commands.index import CommandMixin

import threading


class LogMixin(CommandMixin('log')):

    log_lock = threading.Lock()


    def log_init(self, options, task = None, log_key = None, worker = None):
        if not options:
            options = {}

        if self.log_result:
            with self.log_lock:
                if log_key is None or log_key == '<none>':
                    self.log_entry = self._log.create(None, {
                        'command': self.get_full_name()
                    })
                else:
                    self.log_entry = self._log.retrieve(log_key)

                self.log_entry.user = self.active_user

                search_config, secrets = self.split_secrets()
                self.log_entry.config = search_config
                self.log_entry.secrets = secrets

                self.log_entry.status = self._log.model.STATUS_RUNNING
                if task:
                    self.log_entry.worker = worker
                    self.log_entry.task_id = task.request.id

                self.log_entry.save()

        return self.log_entry.name if self.log_result else '<none>'


    def log_message(self, data, log = True):
        def _create_log_message(command, data, _log):
            if getattr(command, 'log_entry', None) and _log:
                command.log_entry.messages.create(data = data)

            if command.exec_parent:
                _create_log_message(command.exec_parent, data, True)

        if self.log_result:
            with self.log_lock:
                _create_log_message(self, data, log)


    def log_status(self, status, check_log_result = False, schedule = None):
        if not check_log_result or self.log_result:
            with self.log_lock:
                if getattr(self, 'log_entry', None):
                    if schedule:
                        self.log_entry.schedule_id = schedule

                    self.log_entry.set_status(status)
                    self.log_entry.save()

    def get_status(self):
        return self.log_entry.status if self.log_result else None
