from systems.command.index import CommandMixin


class LogMixin(CommandMixin('log')):

    def log_init(self, options, task = None):
        if not options:
            options = {}

        self.log_entry = self._log.create(None,
            command = self.get_full_name()
        )
        self.log_entry.user = self.active_user
        self.log_entry.config = options

        if task:
            self.log_entry.scheduled = True
            self.log_entry.task_id = task.request.id

        self.log_entry.save()

    def log_message(self, data):
        def _create_log_message(command, data):
            if getattr(command, 'log_entry', None):
                command.log_entry.messages.create(data = data)

            if command.exec_parent:
                _create_log_message(command.exec_parent, data)

        _create_log_message(self, data)

    def log_status(self, status):
        self.log_entry.set_status(status)
        self.log_entry.save()
