from django.core.management.base import CommandError

from .base import DataMixin
from data.project import models

import re
import json


class ProjectMixin(DataMixin):

    def parse_project_provider_name(self, optional = False, help_text = 'project resource provider'):
        self._parse_variable('project_provider_name', str, help_text, optional)

    @property
    def project_provider_name(self):
        return self.options.get('project_provider_name', None)

    @property
    def project_provider(self):
        if not getattr(self, '_project_provider', None):
            self._project_provider = self.get_project(self.project_provider_name)
        return self._project_provider


    def parse_project_name(self, optional = False, help_text = 'unique environment project name'):
        self._parse_variable('project_name', str, help_text, optional)

    @property
    def project_name(self):
        return self.options.get('project_name', None)

    @property
    def project(self):
        self._data_project = self._load_instance(
            self._project, self.project_name, 
            getattr(self, '_data_project', None)
        )
        return self._data_project


    def parse_project_reference(self, optional = False, help_text = 'unique environment project name'):
        self._parse_variable('project_reference', str, help_text, optional)

    @property
    def project_reference(self):
        return self.options.get('project_reference', None)

    @property
    def projects(self):
        if not getattr(self, '_data_projects', None):
            self._data_projects = self.get_projects_by_reference(self.project_reference)
        return self._data_projects


    def parse_project_fields(self, optional = False, help_callback = None):
        self._parse_fields(self._project, 'project_fields', optional, 
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


    @property
    def _project(self):
        return models.Project.facade


    def get_projects_by_reference(self, reference = None, error_on_empty = True):
        project_results = []
        if reference and reference != 'all':
            matches = re.search(r'^([^\=]+)\s*\=\s*(.+)', reference)

            if matches:
                field = matches.group(1)
                value = matches.group(2)

                if field != 'state':
                    projects = self._project.query(**{ field: value })
                else:
                    projects = self._project.all()
                    states = [value]
                    
                if len(projects) > 0:
                    project_results.extend(self.get_projects(
                        instances = list(projects), 
                        states = states
                    ))
            else:
                project = self._project.retrieve(reference)
                if project:
                    project_results.extend(self.get_projects(instances = project))
        else:
            project_results.extend(self.get_projects())
        
        if error_on_empty and not project_results:
            if reference:
                self.error("No projects were found: {}".format(reference))
            else:
                self.error("No projects were found")
        
        return project_results

    def get_projects(self, names = [], instances = [], states = None):
        project_items = []
        projects = []

        if not getattr(self, '_data_project_cache', None):
            self._data_project_cache = {}

        if isinstance(names, str):
            names = [names]
        
        if names:
            project_items.extend(names)

        if not isinstance(instances, (list, tuple)):
            instances = [instances]

        if instances:
            project_items.extend(instances)

        if states and not isinstance(states, (list, tuple)):
            states = [states]

        if not project_items and not names and not instances and not states:
            project_items = self._project.all()            

        def init_project(project, state):
            if isinstance(project, str):
                project = self._project.retrieve(project)
            if project:
                if not project.name in self._data_project_cache:
                    if isinstance(project.config, str):
                        project.config = json.loads(project.config)
                    
                    project.project_provider = self.get_project(project.type, project = project)
                    project.state = None
                    self._data_project_cache[project.name] = project
                else:
                    project = self._data_project_cache[project.name]

                if not states or project.state in states:
                    projects.append(project)
            else:
                self.error("Project {} does not exist".format(name))

        self.run_list(project_items, init_project)
        return projects
