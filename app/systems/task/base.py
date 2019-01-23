from django.conf import settings

from settings import Roles
from systems.command import providers

import os
import threading
import string
import random


class TaskResult(object):

    def __init__(self, type):
        self.type = type

    def __str__(self):
        return "[{}]".format(self.type)


class BaseTaskProvider(providers.BaseCommandProvider):

    def __init__(self, name, command, project, config):
        super().__init__(name, command)

        self.project = project
        self.config = config

        self.thread_lock = threading.Lock()

        self.provider_type = 'task'
        self.provider_options = settings.TASK_PROVIDERS


    def check_access(self):
        if 'roles' in self.config:
            if not self.command.check_access(Roles.admin, self.config['roles']):
                return False
        return True


    def get_requirements(self):
        requirements = self.default_requirements()

        if 'requirements' in self.config:
            for file_name in self.config['requirements']:
                requirements.extend(self.project.parse_requirements(file_name))
        
        return requirements
    
    def default_requirements(self):
        # Override in subclass
        return []


    def exec(self, servers, params = {}):
        results = TaskResult(self.name)
        servers = [servers] if not isinstance(servers, (list, tuple)) else servers
        self.execute(results, servers, params)
        return results

    def execute(self, results, servers, params):
        # Override in subclass
        pass


    def get_path(self, path):
        return os.path.join(self.get_project_path(), path)


    def get_project(self):
        return self.project.project

    def get_project_path(self):
        return self.project.project_path(self.get_project().name)


    def generate_name(self, length = 32):
        chars = string.ascii_lowercase + string.digits
        return ''.join(random.SystemRandom().choice(chars) for _ in range(length))
