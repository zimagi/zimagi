from systems.commands.index import CommandMixin

import multiprocessing


class LogMixin(CommandMixin('log')):

    log_lock = multiprocessing.Lock()


    def log_init(self, options, task = None, log_key = None):
        if not options:
            options = {}

        with self.log_lock:
            if log_key is None:
                self.log_entry = self._log.create(None,
                    command = self.get_full_name()
                )
            else:
                self.log_entry = self._log.retrieve(log_key)

            self.log_entry.user = self.active_user
            self.log_entry.config = options
            self.log_entry.status = None
            if task:
                self.log_entry.scheduled = True
                self.log_entry.task_id = task.request.id

            self.log_entry.save()

        return self.log_entry.name


    def log_message(self, data):
        def _create_log_message(command, data):
            if getattr(command, 'log_entry', None):
                command.log_entry.messages.create(data = data)

            if command.exec_parent:
                _create_log_message(command.exec_parent, data)

        with self.log_lock:
            _create_log_message(self, data)


    def log_status(self, status):
        with self.log_lock:
            self.log_entry.set_status(status)
            self.log_entry.save()
