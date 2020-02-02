from django.conf import settings

from .base import DataMixin
from data.notification.models import Notification

import json


class NotificationMixin(DataMixin):

    schema = {
        'notification': {
            'model': Notification
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.facade_index['01_notification'] = self._notification


    def parse_notify(self, optional = '--notify', help_text = 'user group names to notify of command results'):
        self.parse_variables('notify', optional, str, help_text,
            value_label = 'GROUP_NAME'
        )

    @property
    def notify(self):
        return self.options.get('notify', [])


    def parse_notify_failure(self, optional = '--notify-fail', help_text = 'user group names to notify of command failures'):
        self.parse_variables('notify_failure', optional, str, help_text,
            value_label = 'GROUP_NAME'
        )

    @property
    def notify_failure(self):
        return self.options.get('notify_failure', [])


    @property
    def recipients(self):
        recipients = {}

        if self.active_user:
            recipients[self.active_user.name] = self.active_user.email

        if groups := self.notify():
            for group in ensure_list(groups):
                for user in self._user.filter(groups__name = group):
                    recipients[user.name] = user.email

        return recipients


    def format_subject(self, command, status):
        return  "{}: {}".format(status, command)

    def format_body(self, command, options, messages = None):
        return "Command: {}\nOptions: {}\n\nMessages: {}".format(
            command,
            json.dumps(options, indent = 2),
            messages if messages else ''
        )
