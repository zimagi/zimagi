from smtplib import SMTPConnectError, SMTPServerDisconnected
from django.conf import settings
from django.core.mail import send_mail
from celery import Task
from celery.utils.log import get_task_logger

from systems.celery.registry import _unpickle_task
from systems.commands import action
from utility.data import ensure_list

import sys


logger = get_task_logger(__name__)


class CommandTask(Task):

    def __reduce__(self):
        mod = type(self).__module__
        mod = mod if mod and mod in sys.modules else None
        return (_unpickle_task, (self.name, mod), None)


    def exec_command(self, name, options):
        command = action.primary('celery exec_command')
        user = command._user.retrieve(options.pop('_user', settings.ADMIN_USER))
        command._user.set_active_user(user)

        command.exec_local(name, options,
            primary = True,
            task = self
        )


    def clean_interval_schedule(self):
        command = action.primary('celery clean_interval_schedule')

        def run():
            interval_ids = list(command._scheduled_task.filter(interval_id__isnull = False).distinct().values_list('interval_id', flat = True))
            logger.debug("Interval IDs: {}".format(interval_ids))

            for record in command._task_interval.exclude(name__in = interval_ids):
                record.delete()
                logger.info("Deleted unused interval schedule: {}".format(record.get_id()))

        command.run_exclusive('zimagi-task-clean-interval', run,
            error_on_locked = True
        )

    def clean_crontab_schedule(self):
        command = action.primary('celery clean_crontab_schedule')

        def run():
            crontab_ids = list(command._scheduled_task.filter(crontab_id__isnull = False).distinct().values_list('crontab_id', flat = True))
            logger.debug("Crontab IDs: {}".format(crontab_ids))

            for record in command._task_crontab.exclude(name__in = crontab_ids):
                record.delete()
                logger.info("Deleted unused crontab schedule: {}".format(record.get_id()))

        command.run_exclusive('zimagi-task-clean-crontab', run,
            error_on_locked = True
        )

    def clean_datetime_schedule(self):
        command = action.primary('celery clean_datetime_schedule')

        def run():
            datetime_ids = list(command._scheduled_task.filter(clocked_id__isnull = False).distinct().values_list('clocked_id', flat = True))
            logger.debug("Datetime IDs: {}".format(datetime_ids))

            for record in command._task_datetime.exclude(name__in = datetime_ids):
                record.delete()
                logger.info("Deleted unused datetime schedule: {}".format(record.get_id()))

        command.run_exclusive('zimagi-task-clean-datetime', run,
            error_on_locked = True
        )


    def send_notification(self, recipient, subject, body):
        if settings.EMAIL_HOST and settings.EMAIL_HOST_USER:
            try:
                html_body = body.replace("\n", '<br/>')
                html_body = html_body.replace(" ", '&nbsp;')
                html_body = '<font face="Courier New, Courier, monospace">{}</font>'.format(html_body)

                send_mail(
                    subject,
                    body,
                    settings.EMAIL_HOST_USER,
                    ensure_list(recipient),
                    html_message = html_body
                )
                logger.info("Notification message '{}' sent to: {}".format(subject, recipient))

            except SMTPConnectError as e:
                logger.error("Notification delivery failed: {}".format(e))
                raise e

            except SMTPServerDisconnected as e:
                logger.error("Notification service disconnected: {}".format(e))
                raise e

            except Exception as e:
                logger.error("Notification error: {}".format(e))
                raise e
