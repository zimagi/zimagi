from django.conf import settings
from django.core.management.base import CommandError

from . import DataMixin
from data.project.models import Project
from utility import config

import re
import json


class ProjectMixin(DataMixin):

    def __init__(self, *args, **kwargs):
        super().__init__(stdout, stderr, no_color)
        self.facade_index['01_project'] = self._project


    def parse_project_provider_name(self, optional = False, help_text = 'project resource provider (default @project_provider|internal)'):
        self.parse_variable('project_provider_name', optional, str, help_text, 'NAME')

    @property
    def project_provider_name(self):
        name = self.options.get('project_provider_name', None)
        if not name:
            name = self.get_config('project_provider', required = False)
        if not name:
            name = config.Config.string('PROJECT_PROVIDER', 'internal')
        return name

    @property
    def project_provider(self):
        return self.get_provider('project', self.project_provider_name)


    def parse_project_name(self, optional = False, help_text = 'unique environment project name'):
        self.parse_variable('project_name', optional, str, help_text, 'NAME')

    @property
    def project_name(self):
        return self.options.get('project_name', settings.CORE_PROJECT)

    @property
    def project(self):
        return self.get_instance(self._project, self.project_name)


    def parse_project_reference(self, optional = False, help_text = 'unique environment project name'):
        self.parse_variable('project_reference', optional, str, help_text, 'REFERENCE')

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


    def parse_profile_name(self, optional = False, help_text = 'project profile name'):
        self.parse_variable('profile_name', optional, str, help_text, 'NAME')

    @property
    def profile_name(self):
        return self.options.get('profile_name', None)

    def parse_profile_fields(self, optional = False, help_callback = None):
        def default_help_callback():
            return ["Profile parameters"]

        if not help_callback:
            help_callback = default_help_callback
        
        self.parse_fields(None, 'profile_fields', optional,
            help_callback = help_callback
        )

    @property
    def profile_fields(self):
        return self.options.get('profile_fields', {})

    def parse_profile_components(self, flag = '--components', help_text = 'one or more project profile component names'):
        self.parse_variables('profile_components', flag, str, help_text, 'NAME')

    @property
    def profile_component_names(self):
        return self.options.get('profile_components', [])


    def parse_task_name(self, optional = False, help_text = 'project task name'):
        self.parse_variable('task_name', optional, str, help_text, 'NAME')

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
        return self.facade(Project.facade)
