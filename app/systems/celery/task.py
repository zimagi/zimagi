from smtplib import SMTPConnectError, SMTPServerDisconnected
from django.conf import settings
from django.core.mail import send_mail
from celery import Task
from celery.exceptions import TaskError
from celery.utils.log import get_task_logger

from data.schedule.models import (
    ScheduledTask,
    TaskInterval,
    TaskCrontab,
    TaskDatetime
)
from systems.command.types.action import ActionCommand
from utility.data import ensure_list

import sys
import io
import json


logger = get_task_logger(__name__)


class CommandTask(Task):

    def __init__(self):
        self.command = ActionCommand('celery')


    def _capture_output(self, function):
        old_stdout = sys.stdout
        sys.stdout = mystdout = io.StringIO()

        try:
            function()

        except Exception as e:
            raise TaskError("{}: {}".format(str(e), mystdout.getvalue()))

        finally:
            sys.stdout = old_stdout

        return mystdout.getvalue()


    def exec_command(self, name, options):
        def run():
            user = self.command._user.retrieve(options.pop('_user', settings.ADMIN_USER))
            self.command._user.set_active_user(user)

            self.command.exec_local(name, options,
                task = self
            )
        return self._capture_output(run)


    def clean_interval_schedule(self):
        def run():
            interval_ids = list(self.command._scheduled_task.filter(interval_id__isnull=False).distinct().values_list('interval_id', flat=True))
            logger.debug("Interval IDs: {}".format(interval_ids))

            for record in self.command._interval.exclude(id__in = interval_ids):
                record.delete()
                logger.info("Deleted unused interval schedule: {}".format(record.id))

        return self._capture_output(run)


    def clean_crontab_schedule(self):
        def run():
            crontab_ids = list(self.command._scheduled_task.filter(crontab_id__isnull=False).distinct().values_list('crontab_id', flat=True))
            logger.debug("Crontab IDs: {}".format(crontab_ids))

            for record in self.command._crontab.exclude(id__in = crontab_ids):
                record.delete()
                logger.info("Deleted unused crontab schedule: {}".format(record.id))

        return self._capture_output(run)


    def clean_datetime_schedule(self):
        def run():
            datetime_ids = list(self.command._scheduled_task.filter(clocked_id__isnull=False).distinct().values_list('clocked_id', flat=True))
            logger.debug("Datetime IDs: {}".format(datetime_ids))

            for record in self.command._clocked.exclude(id__in = datetime_ids):
                record.delete()
                logger.info("Deleted unused datetime schedule: {}".format(record.id))

        return self._capture_output(run)


    def send_notification(self, recipient, subject, body):
        def run():
            if settings.EMAIL_HOST and settings.EMAIL_HOST_USER:
                try:
                    send_mail(
                        subject,
                        body,
                        settings.EMAIL_HOST_USER,
                        ensure_list(recipient)
                    )
                except SMTPConnectError as e:
                    raise self.retry(exc = e)
                except SMTPServerDisconnected as e:
                    raise self.retry(exc = e)

        return self._capture_output(run)