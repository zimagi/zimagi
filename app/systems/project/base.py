from pip._internal import main as package

from django.conf import settings

from systems.command import providers

import pip
import os
import pathlib
import threading
import yaml


class ProjectResult(object):

    def __init__(self, type, config,
        name = None, 
        remote = None,
        reference = None
    ):
        self.type = type
        self.config = config
        self.name = name
        self.remote = remote
        self.reference = reference

    def __str__(self):
        return "[{}]> {} ({}[{}])".format(
            self.type,
            self.name,
            self.remote,
            self.reference       
        )


class BaseProjectProvider(providers.BaseCommandProvider):

    def __init__(self, name, command, project = None):
        super().__init__(name, command)
        
        self.project = project
        self.thread_lock = threading.Lock()

        self.provider_type = 'project'
        self.provider_options = settings.PROJECT_PROVIDERS


    def project_path(self, name):
        env = self.command.curr_env
        path = os.path.join(settings.PROJECT_BASE_PATH, env.name, name)
        pathlib.Path(path).mkdir(parents = True, exist_ok = True)
        return path


    def create_project(self, config, complete_callback = None):
        self.config = config
        
        self.provider_config()
        self.validate()

        project = ProjectResult(self.name, config)

        for key, value in self.config.items():
            if hasattr(project, key) and key not in ('type', 'config'):
                setattr(project, key, value)

        self.initialize_project(project)

        if complete_callback and callable(complete_callback):
            complete_callback(project)
        
        return project

    def initialize_project(self, project):
        # Override in subclass
        pass

    def update_project(self, fields = {}):
        # Override in subclass
        pass

    def destroy_project(self):
        # Override in subclass
        pass


    def provision(self, servers):
        requirements = [ req for req in self.load_file('requirements.txt').split("\n") if req and req[0].strip() != '#' ]
        success, stdout, stderr = self.command.sh(['pip3', 'install'] + requirements)
        self.command.data('success', success)
        self.command.data('stdout', str(stdout))
        self.command.data('stderr', str(stderr))


    def load_file(self, file_name):
        if not self.project:
            self.command.error("Loading file in project requires a valid project instance given to provider on initialization")

        project_path = self.project_path(self.project.name)
        path = os.path.join(project_path, file_name)
        content = None

        if os.path.exists(path):
            with open(path, 'r') as file:
                content = file.read()
        
        return content

    def load_yaml(self, file_name):
        return yaml.load(self.load_file(file_name))


    def save_file(self, file_name, content = ''):
        if not self.project:
            self.command.error("Saving file in project requires a valid project instance given to provider on initialization")

        project_path = self.project_path(self.project.name)
        path = os.path.join(project_path, file_name)
        
        pathlib.Path(path).mkdir(parents = True, exist_ok = True)

        with open(path, 'w') as file:
            file.write(content)
        
        return content

    def save_yaml(self, file_name, data = {}):
        return self.save_file(file_name, yaml.dump(data))
