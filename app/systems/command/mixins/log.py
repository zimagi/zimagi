from data.log.models import Log
from .base import DataMixin


class LogMixin(DataMixin):

    schema = {
        'log': {
            'model': Log
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.facade_index['02_log'] = self._log


    def log_init(self, options = {}):
        self.log_entry = self._log.create(None,
            command = self.get_full_name()
        )
        self.log_entry.user = self.active_user
        self.log_entry.config = options
        self.log_entry.save()

    def log_message(self, data):
        def _create_log_message(command, data):
            if getattr(command, 'log_entry', None):
                with self._log.thread_lock:
                    command.log_entry.messages.create(data = data)

            if command.parent_instance:
                _create_log_message(command.parent_instance, data)

        _create_log_message(self, data)

    def log_status(self, status):
        self.log_entry.set_status(status)
        self.log_entry.save()
