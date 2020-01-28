from django.conf import settings
from django.core.mail import send_mail
from celery import Task
from celery.exceptions import TaskError
from celery.utils.log import get_task_logger
from django_celery_beat.models import IntervalSchedule, CrontabSchedule, ClockedSchedule, PeriodicTask

from settings.roles import Roles
from systems.command.types.action import ActionCommand
from systems.plugins import data
from utility.data import ensure_list

import os
import sys
import io
import threading
import string
import random
import re
import json


logger = get_task_logger(__name__)


class CeleryTask(Task):

    def __init__(self):
        self.command = ActionCommand('celery')


    def exec_command(self, name, options):
        old_stdout = sys.stdout
        sys.stdout = mystdout = io.StringIO()

        try:
            user = self.command._user.retrieve(options.pop('_user', settings.ADMIN_USER))
            self.command._user.set_active_user(user)

            self.command.exec_local(name, options,
                task = self
            )

        except Exception as e:
            raise TaskError(mystdout.getvalue())

        finally:
            sys.stdout = old_stdout

        return mystdout.getvalue()


    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        notifications = {}

        subject = "Status {} detected for task: {}".format(status, task_id)
        message = "Arguments: {}\nKeywords: {}\n\nMessages: {}".format(
            " ".join(args),
            json.dumps(kwargs, indent = 2),
            retval['messages'] if retval and 'messages' in retval else ''
        )

        if self.command.active_user:
            logger.debug("Active user: {}".format(self.command.active_user))
            notifications[self.command.active_user.name] = self.command.active_user.email

        if 'notify' in kwargs and kwargs['notify']:
            for group in ensure_list(kwargs['notify']):
                for user in self.command._user.filter(groups__name = group):
                    notifications[user.name] = user.email

        logger.debug("Notifications: {}".format(", ".join(notifications.values())))

        if status == 'SUCCESS':
            logger.debug("\nTask: {}\n{}".format(task_id, message))
        else:
            logger.debug("\nTask: {}\n{}".format(task_id, message))
            logger.error("{}: {}".format(subject, str(einfo)))

            if settings.EMAIL_HOST and settings.EMAIL_HOST_USER and notifications:
                send_mail(subject, message, settings.EMAIL_HOST_USER, list(notifications.values()))


    def clean_interval_schedule(self):
        old_stdout = sys.stdout
        sys.stdout = mystdout = io.StringIO()

        try:
            interval_ids = list(PeriodicTask.objects.filter(interval_id__isnull=False).distinct().values_list('interval_id', flat=True))
            logger.debug("Interval IDs: {}".format(interval_ids))

            for record in IntervalSchedule.objects.exclude(id__in = interval_ids):
                record.delete()
                logger.info("Deleted unused interval schedule: {}".format(record.id))

        except Exception as e:
            raise TaskError(mystdout.getvalue())

        finally:
            sys.stdout = old_stdout

        return mystdout.getvalue()


    def clean_crontab_schedule(self):
        old_stdout = sys.stdout
        sys.stdout = mystdout = io.StringIO()

        try:
            crontab_ids = list(PeriodicTask.objects.filter(crontab_id__isnull=False).distinct().values_list('crontab_id', flat=True))
            logger.debug("Crontab IDs: {}".format(crontab_ids))

            for record in CrontabSchedule.objects.exclude(id__in = crontab_ids):
                record.delete()
                logger.info("Deleted unused crontab schedule: {}".format(record.id))

        except Exception as e:
            raise TaskError(mystdout.getvalue())

        finally:
            sys.stdout = old_stdout

        return mystdout.getvalue()


    def clean_datetime_schedule(self):
        old_stdout = sys.stdout
        sys.stdout = mystdout = io.StringIO()

        try:
            datetime_ids = list(PeriodicTask.objects.filter(clocked_id__isnull=False).distinct().values_list('clocked_id', flat=True))
            logger.debug("Datetime IDs: {}".format(datetime_ids))

            for record in ClockedSchedule.objects.exclude(id__in = datetime_ids):
                record.delete()
                logger.info("Deleted unused datetime schedule: {}".format(record.id))

        except Exception as e:
            raise TaskError(mystdout.getvalue())

        finally:
            sys.stdout = old_stdout

        return mystdout.getvalue()


class TaskResult(object):

    def __init__(self, type):
        self.type = type
        self.data = None
        self.message = None

    def __str__(self):
        return "[{}]".format(self.type)


class BaseProvider(data.BasePluginProvider):

    def __init__(self, type, name, command, module, config):
        super().__init__(type, name, command)

        self.module = module
        self.config = config

        self.roles = self.config.pop('roles', None)
        self.module_override = self.config.pop('module', None)

        self.thread_lock = threading.Lock()


    def check_access(self):
        if self.roles:
            if not self.command.check_access_by_groups(self.module.instance, [Roles.admin, self.roles]):
                return False
        return True


    def exec(self, params = {}):
        results = TaskResult(self.name)
        self.execute(results, params)
        return results

    def execute(self, results, params):
        # Override in subclass
        pass


    def get_path(self, path):
        return os.path.join(self.get_module_path(), path)


    def get_module(self):
        return self.module.instance

    def get_module_path(self):
        instance = self.get_module()
        if self.module_override:
            instance = self.command.get_instance(instance.facade, self.module_override)
        return instance.provider.module_path(instance.name)


    def generate_name(self, length = 32):
        chars = string.ascii_lowercase + string.digits
        return ''.join(random.SystemRandom().choice(chars) for _ in range(length))
