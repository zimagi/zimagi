from django.conf import settings

from .base import BaseProjectProvider

import pygit2
import shutil
import pathlib
import os


class Git(BaseProjectProvider):

    def provider_config(self, type = None):
        self.requirement('name', help = 'Unique name of project in environment')
        self.requirement('remote', help = 'Git remote to clone and pull updates')
        
        self.option('reference', 'master', help = 'Git branch, tag, or commit reference', config_name = 'git_reference')


    def initialize_project(self, project):
        project_path = self.project_path(project.name)

        if (os.path.exists(project_path)):
            repository = pygit2.Repository(project_path)
            repository.remotes.set_url("origin", project.remote)
            self._pull(repository, branch_name = project.reference)
        else:
            repository = pygit2.clone_repository(project.remote, project_path, checkout_branch = project.reference)
        
        repository.update_submodules(init = True)
    

    def update_project(self, fields = {}):
        if not self.project:
            self.command.error("Updating project requires a valid project instance given to provider on initialization")
        
        repository = pygit2.Repository(self.project_path(self.project.name))

        if 'remote' in fields:
            self.project.remote = fields['remote']
            repository.remotes.set_url("origin", self.project.remote)

        if 'reference' in fields:
            self.project.reference = fields['reference']

        self._pull(repository, branch_name = self.project.reference)
        repository.update_submodules(init = True)


    def destroy_project(self):
        if not self.project:
            self.command.error("Destroying project requires a valid project instance given to provider on initialization")
        
        project_path = self.project_path(self.project.name)
        shutil.rmtree(pathlib.Path(project_path), ignore_errors = True)


    def _pull(self, repository, remote_name = 'origin', branch_name = 'master'):
        repository.checkout(repository.lookup_branch(branch_name))

        remote = repository.remotes[remote_name]
        remote.fetch()

        remote_reference = repository.lookup_reference('refs/remotes/{}/{}'.format(remote_name, branch_name)).target
        merge_result, _ = repository.merge_analysis(remote_reference)
            
        if merge_result & pygit2.GIT_MERGE_ANALYSIS_UP_TO_DATE:
            return
            
        elif merge_result & pygit2.GIT_MERGE_ANALYSIS_FASTFORWARD:
            repository.checkout_tree(repository.get(remote_reference))
            head_reference = repository.lookup_reference('refs/heads/{}'.format(branch_name))
            head_reference.set_target(remote_reference)
            repository.head.set_target(remote_reference)
            
        elif merge_result & pygit2.GIT_MERGE_ANALYSIS_NORMAL:
            repository.merge(remote_reference)
            user = repository.default_signature
            tree = repository.index.write_tree()
            commit = repository.create_commit('HEAD',
                user,
                user,
                'Merge',
                tree,
                [repository.head.target, remote_reference]
            )
            repository.state_cleanup()
                
        else:
            self.command.error("Unable to pull remote changes from remote")
