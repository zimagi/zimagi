from django.conf import settings

from .base import BaseProjectProvider

import pygit2
import shutil
import pathlib
import os


class Git(BaseProjectProvider):

    def provider_config(self, type = None):
        self.requirement(str, 'remote', help = 'Git remote to clone and pull updates')
        
        self.option(str, 'reference', 'master', help = 'Git branch, tag, or commit reference', config_name = 'git_reference')


    def initialize_instance(self, instance, created):
        if created:
            return self._init_repository(instance)
        return self._update_repository(instance)

    def _init_repository(self, instance):
        project_path = self.project_path(instance.name)

        if (os.path.exists(os.path.join(project_path, '.git'))):
            repository = pygit2.Repository(project_path)
            repository.remotes.set_url("origin", instance.remote)
            self._pull(repository, branch_name = instance.reference)
        else:
            repository = pygit2.clone_repository(instance.remote, project_path, checkout_branch = instance.reference)
        
        repository.update_submodules(init = True)
    
    def _update_repository(self, instance):
        repository = pygit2.Repository(self.project_path(instance.name))
        repository.remotes.set_url("origin", instance.remote)

        self._pull(repository, branch_name = instance.reference)
        repository.update_submodules(init = True)


    def finalize_instance(self, instance):
        project_path = self.project_path(instance.name)
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
