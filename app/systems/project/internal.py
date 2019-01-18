from django.conf import settings

from .base import BaseProjectProvider, ProjectResult


class Internal(BaseProjectProvider):

    def project_path(self, name):
        return settings.APP_DIR

    def create_project(self, config, complete_callback = None):
        return ProjectResult(self.name, config)
