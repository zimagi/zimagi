import sys
from smtplib import SMTPConnectError, SMTPServerDisconnected

from celery import Task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.mail import send_mail
from systems.celery.registry import _unpickle_task
from systems.commands import action
from utility.data import ensure_list

logger = get_task_logger(__name__)


class CommandTask(Task):
    def __reduce__(self):
        mod = type(self).__module__
        mod = mod if mod and mod in sys.modules else None
        return (_unpickle_task, (self.name, mod), None)

    def exec_command(self, name, options):
        command = action.primary("celery exec_command")
        user = command._user.retrieve(options.pop("_user", settings.ADMIN_USER))
        command._user.set_active_user(user)

        command.exec_local(name, options, primary=True, task=self)
        command.export_profiler_data()

    def send_notification(self, recipient, subject, body, wrap_body=True):
        if settings.EMAIL_HOST and settings.EMAIL_HOST_USER:
            try:
                if wrap_body:
                    html_body = body.replace("\n", "<br/>")
                    html_body = html_body.replace(" ", "&nbsp;")
                    html_body = f'<font face="Courier New, Courier, monospace">{html_body}</font>'
                else:
                    html_body = body

                send_mail(subject, body, settings.EMAIL_HOST_USER, ensure_list(recipient), html_message=html_body)
                logger.info(f"Notification message '{subject}' sent to: {recipient}")

            except SMTPConnectError as e:
                logger.error(f"Notification delivery failed: {e}")
                raise e

            except SMTPServerDisconnected as e:
                logger.error(f"Notification service disconnected: {e}")
                raise e

            except Exception as e:
                logger.error(f"Notification error: {e}")
                raise e
