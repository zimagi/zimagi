from django.conf import settings
from django.core.management.base import CommandError

from . import DataMixin
from data.project import models

import re
import json


class ProjectMixin(DataMixin):

    def parse_project_provider_name(self, optional = False, help_text = 'project resource provider'):
        self.parse_variable('project_provider_name', optional, str, help_text)

    @property
    def project_provider_name(self):
        return self.options.get('project_provider_name', None)

    @property
    def project_provider(self):
        return self.get_provider('project', self.project_provider_name)


    def parse_project_name(self, optional = False, help_text = 'unique environment project name'):
        self.parse_variable('project_name', optional, str, help_text)

    @property
    def project_name(self):
        return self.options.get('project_name', settings.CORE_PROJECT)

    @property
    def project(self):
        return self.get_instance(self._project, self.project_name)


    def parse_project_reference(self, optional = False, help_text = 'unique environment project name'):
        self.parse_variable('project_reference', optional, str, help_text)

    @property
    def project_reference(self):
        return self.options.get('project_reference', None)

    @property
    def projects(self):
        return self.get_instances_by_reference(self._project, self.project_reference)

    def parse_project_fields(self, optional = False, help_callback = None):
        self.parse_fields(self._project, 'project_fields', optional, 
            (
                'created', 
                'updated', 
                'environment',
                'config'
            ),
            help_callback
        )

    @property
    def project_fields(self):
        return self.options.get('project_fields', {})


    def parse_task_name(self, optional = False, help_text = 'project task name'):
        self.parse_variable('task_name', optional, str, help_text)

    @property
    def task_name(self):
        return self.options.get('task_name', None)

    def parse_task_params(self, optional = False, help_callback = None):
        def default_help_callback():
            return ["Task parameters"]

        if not help_callback:
            help_callback = default_help_callback
        
        self.parse_fields(None, 'task_params', optional,
            help_callback = help_callback
        )

    @property
    def task_params(self):
        return self.options.get('task_params', {})


    @property
    def _project(self):
        return models.Project.facade


    def initialize_instance(self, facade, project):
        if facade.name == 'project':
            project.provider = self.get_provider('project', project.type, project = project)
            project.state = None
