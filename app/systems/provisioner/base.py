from django.conf import settings

from systems.command import providers

import os
import pathlib
import threading


class ProvisionerResult(object):

    def __init__(self, type):
        self.type = type

    def __str__(self):
        return "[{}]".format(self.type)


class BaseProvisionerProvider(providers.BaseCommandProvider):

    def __init__(self, name, command, project):
        super().__init__(name, command)

        self.project = project        
        self.thread_lock = threading.Lock()

        self.provider_type = 'provisioner'
        self.provider_options = settings.PROVISIONER_PROVIDERS


    def provision(self):
        results = ProvisionerResult(self.name)
        return self.provision_project(results)

    def provision_project(self, results):
        # Override in subclass
        pass


    def get_project(self):
        return self.project.project

    def get_project_path(self):
        return self.project.project_path(self.get_project().name)
