from django.conf import settings

from systems.command import providers

import os
import pathlib
import threading


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
