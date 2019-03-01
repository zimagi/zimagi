from django.conf import settings

from . import DataMixin
from data.log.models import Log


class LogMixin(DataMixin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.facade_index['01_log'] = self._log


    def parse_log_name(self, optional = False, help_text = 'unique environment log entry name'):
        self.parse_variable('log_name', optional, str, help_text, 
            value_label = 'NAME'
        )

    @property
    def log_name(self):
        return self.options.get('log_name', None)


    @property
    def log(self):
        return self.get_instance(self._log, self.log_name)


    def parse_log_order(self, optional = '--order', help_text = 'log ordering fields (~field for desc)'):
        self.parse_variables('log_order', optional, str, help_text, 
            value_label = '[~]FIELD'
        )

    @property
    def log_order(self):
        return self.options.get('log_order', [])


    def parse_log_search(self, optional = True, help_text = 'log search fields'):
        self.parse_variables('log_search', optional, str, help_text, 
            value_label = 'REFERENCE'
        )

    @property
    def log_search(self):
        return self.options.get('log_search', [])

    @property
    def log_instances(self):
        return self.search_instances(self._log, self.log_search)


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

