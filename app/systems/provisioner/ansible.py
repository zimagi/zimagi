from django.conf import settings

from .base import BaseProvisionerProvider


class Ansible(BaseProvisionerProvider):

    def provision_project(self, results):
        project_path = self.project.project_path(self.project.name)
        
