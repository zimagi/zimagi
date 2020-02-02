from django.conf import settings

from .base import DataMixin


class NotificationMixin(DataMixin):

    def parse_notify(self, optional = '--notify', help_text = 'user group names to notify of results when scheduled'):
        self.parse_variables('notify', optional, str, help_text,
            value_label = 'GROUP_NAME'
        )

    @property
    def notify(self):
        return self.options.get('notify', [])
