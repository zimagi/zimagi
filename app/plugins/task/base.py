from django.conf import settings
from django.core.mail import send_mail
from celery import Task
from celery.exceptions import TaskError
from celery.utils.log import get_task_logger

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
        subject = "Status {} detected for task: {}".format(status, task_id)
        message = "Arguments: {}\nKeywords: {}\n\nMessages: {}".format(
            " ".join(args),
            json.dumps(kwargs, indent = 2),
            retval['messages']
        )

        logger.debug("Active user: {}".format(self.command.active_user))

        notifications = {
            self.command.active_user.name: self.command.active_user.email
        }
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

            if settings.EMAIL_HOST and settings.EMAIL_HOST_USER:
                send_mail(subject, message, settings.EMAIL_HOST_USER, list(notifications.values()))


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
