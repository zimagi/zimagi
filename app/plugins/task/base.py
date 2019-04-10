from django.conf import settings

from settings.roles import Roles
from systems.plugins import data

import os
import threading
import string
import random


class TaskResult(object):

    def __init__(self, type):
        self.type = type

    def __str__(self):
        return "[{}]".format(self.type)


class BaseProvider(data.BasePluginProvider):

    def __init__(self, type, name, command, module, config):
        super().__init__(type, name, command)

        self.module = module
        self.config = config

        self.thread_lock = threading.Lock()


    def check_access(self):
        if 'roles' in self.config:
            if not self.command.check_access_by_groups(self.module.instance, [Roles.admin, self.config['roles']]):
                return False
        return True


    def exec(self, params = {}):
        results = TaskResult(self.name)
        self.config.pop('roles', None)
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
        return self.module.module_path(self.get_module().name)


    def generate_name(self, length = 32):
        chars = string.ascii_lowercase + string.digits
        return ''.join(random.SystemRandom().choice(chars) for _ in range(length))
