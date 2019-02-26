from django.conf import settings

from . import DataMixin
from data.log.models import Log


class LogMixin(DataMixin):

    def __init__(self, *args, **kwargs):
        super().__init__(stdout, stderr, no_color)
        self.facade_index['01_log'] = self._log


    def parse_log_name(self, optional = False, help_text = 'unique environment log entry name'):
        self.parse_variable('log_name', optional, str, help_text, 'NAME')

    @property
    def log_name(self):
        return self.options.get('log_name', None)

    @property
    def log(self):
        return self.get_instance(self._log, self.log_name)


    @property
    def _log(self):
        return self.facade(Log.facade)


    def log(self, command, config = {}):
        instance = self._log.create(None, 
            user = self.active_user,
            command = command
        )
        instance.config = config
        instance.save()
        return instance

