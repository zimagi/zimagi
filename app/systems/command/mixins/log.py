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


    def log_exec(self, command, config = {}):
        instance = self._log.create(None,
            user = self.active_user,
            command = command
        )
        instance.config = config
        instance.save()
        return instance
