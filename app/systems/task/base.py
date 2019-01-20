from django.conf import settings

from settings import Roles
from systems.command import providers

import os
import pathlib
import shutil
import threading
import string
import random


class TaskResult(object):

    def __init__(self, type):
        self.type = type

    def __str__(self):
        return "[{}]".format(self.type)


class TempSpace(object):

    def __init__(self):
        self.temp_name = self._generate_name()
        self.temp_path = "/tmp/{}".format(self.temp_name)

        self.thread_lock = threading.Lock()
        
        pathlib.Path(self.temp_path).mkdir(mode = 0o700, parents = True, exist_ok = True)

    def _generate_name(self, length = 32):
        chars = string.ascii_lowercase + string.digits
        return ''.join(random.SystemRandom().choice(chars) for _ in range(length))


    def path(self, file_name, directory = None):
        if file_name.startswith(self.temp_path):
            return file_name
        
        if directory:
            temp_path = os.path.join(self.temp_path, directory)
            pathlib.Path(temp_path).mkdir(mode = 0o700, parents = True, exist_ok = True)
        else:
            temp_path = self.temp_path
        
        return os.path.join(temp_path, file_name)


    def load(self, file_name, directory = None, binary = False):
        tmp_path = self.path(file_name, directory = directory)
        operation = 'rb' if binary else 'r'
        content = None

        with self.thread_lock:        
            if os.path.exists(tmp_path):
                with open(tmp_path, operation) as file:
                    content = file.read()
        
        return content

    def save(self, content, directory = None, extension = None, binary = False):
        file_name = self._generate_name()
        tmp_path = self.path(file_name, directory = directory)
        operation = 'wb' if binary else 'w'

        if extension:
            tmp_path = "{}.{}".format(tmp_path, extension)

        with self.thread_lock:
            with open(tmp_path, operation) as file:
                file.write(content)

            path = pathlib.Path(tmp_path)
            path.chmod(0o700)

        return tmp_path

    def delete(self):
        if self.temp_path.startswith('/tmp/'):
            shutil.rmtree(self.temp_path, ignore_errors = True)


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
