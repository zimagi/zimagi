from django.conf import settings

from .base import BaseProjectProvider

import pygit2
import shutil
import pathlib


class Git(BaseProjectProvider):

    def provider_config(self):
        self.requirement('name', help = 'Unique name of project in environment')
        self.requirement('remote', help = 'Git remote to clone and pull updates')
        
        self.option('reference', 'master', help = 'Git branch, tag, or commit reference')


    def initialize_project(self, project):
        project_path = self.project_path(project.name)
        pygit2.clone_repository(project.remote, project_path, checkout_branch = project.reference)


    def update_project(self, fields = {}):
        if not self.project:
            self.command.error("Updating project requires a valid project instance given to provider on initialization")
        
        repository = pygit2.Repository(self.project_path(self.project.name))

        if 'remote' in fields:
            self.project.remote = fields['remote']
            repository.remotes.set_url("origin", self.project.remote)

        remote = repository.remotes["origin"]
        remote.fetch()

        if 'reference' in fields:
            self.project.reference = fields['reference']

        repository.checkout(repository.lookup_branch(self.project.reference))


    def destroy_project(self):
        if not self.project:
            self.command.error("Destroying project requires a valid project instance given to provider on initialization")
        
        project_path = self.project_path(self.project.name)
        shutil.rmtree(pathlib.Path(project_path), ignore_errors = True)
