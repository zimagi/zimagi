from django.conf import settings

from .base import DataMixin
from data.notification.models import Notification

import json
import re


class NotificationMixin(DataMixin):

    schema = {
        'notification': {
            'model': Notification
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.facade_index['01_notification'] = self._notification


    def parse_notify_failure(self):
        self.parse_flag('notify_failure', '--failure', 'only notify groups on command failure')

    @property
    def notify_failure(self):
        return self.options.get('notify_failure', False)

    def parse_notify_command(self, optional = False, help_text = 'notification command with colons replacing spaces (ex: user:save)'):
        self.parse_variable('notify_command', optional, str, help_text,
            value_label = 'CMD[:SUBCMD[:...]]'
        )

    @property
    def notify_command(self):
        command = self.options.get('notify_command', None)
        if command:
            command = re.sub(r'\s+', ':', command)
        return command

    def parse_notify_groups(self, optional = '--groups', help_text = 'user group names to notify of command results'):
        self.parse_variables('notify_groups', optional, str, help_text,
            value_label = 'GROUP_NAME'
        )

    @property
    def notify_groups(self):
        groups = []

        if group_names := self.options.get('notify_groups', None):
            for name in group_names:
                group = self._group.retrieve(name)
                if not group:
                    group = self.group_provider.store(name, {})
                groups.append(group)

        return groups



    def parse_command_notify(self, optional = '--notify', help_text = 'user group names to notify of command results'):
        self.parse_variables('command_notify', optional, str, help_text,
            value_label = 'GROUP_NAME'
        )

    @property
    def command_notify(self):
        return self.options.get('command_notify', [])


    def parse_command_notify_failure(self, optional = '--notify-fail', help_text = 'user group names to notify of command failures'):
        self.parse_variables('command_notify_failure', optional, str, help_text,
            value_label = 'GROUP_NAME'
        )

    @property
    def command_notify_failure(self):
        return self.options.get('command_notify_failure', [])


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
