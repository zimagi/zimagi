from django.conf import settings
from kombu.exceptions import OperationalError

from .base import DataMixin
from data.notification.models import Notification
from interface.core.tasks import send_notification
from utility.data import ensure_list

import json
import re
import logging


logger = logging.getLogger(__name__)


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


    def load_notification_users(self, success):
        self.notification_users = {}

        def load_groups(groups):
            for group in ensure_list(groups):
                for user in self._user.filter(groups__name = group):
                    if user.email:
                        self.notification_users[user.name] = user.email

        if self.active_user and self.active_user.email:
            self.notification_users[self.active_user.name] = self.active_user.email

        command = re.sub(r'\s+', ':', self.get_full_name())
        notification = self._notification.retrieve(command)

        if notification:
            notification_groups = list(notification.groups.values_list(
                'group__name', flat = True
            ))
            if notification_groups:
                load_groups(notification_groups)

        if groups := self.command_notify:
            load_groups(groups)

        if not success:
            if notification:
                notification_failure_groups = list(notification.failure_groups.values_list(
                    'group__name', flat = True
                ))
                if notification_failure_groups:
                    load_groups(notification_failure_groups)

            if groups := self.command_notify_failure:
                load_groups(groups)

        return list(self.notification_users.values())


    def format_notification_subject(self, success):
        status = 'SUCCESS' if success else 'FAILED'
        return  "{} {}: {}".format(
            settings.EMAIL_SUBJECT_PREFIX,
            status,
            self.get_full_name()
        )

    def format_notification_body(self):
        option_lines = []
        for key, val in self.options.export().items():
            option_lines.append("> {}: {}".format(key, val))

        return "Command: {}\n\nOptions:\n\n{}\n\nMessages:\n\n{}\n\nMore Information:\n\n{}".format(
            self.get_full_name(),
            "\n".join(option_lines),
            "\n".join(self.notification_messages),
            "mcmi log get {}".format(self.log_entry.id)
        )


    def send_notifications(self, success):
        recipients = self.load_notification_users(success)
        subject = self.format_notification_subject(success)
        body = self.format_notification_body()

        def send_mail(recipient):
            try:
                logger.debug("Sending '{}' notification via celery".format(subject))
                send_notification.delay(recipient, subject, body)
            except OperationalError as e:
                logger.debug("Sending '{}' notification now: {}".format(subject, e))
                send_notification(recipient, subject, body)

        self.run_list(recipients, send_mail)
