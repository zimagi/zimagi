from systems.plugins.index import BaseProvider
from utility.temp import temp_dir
from utility.filesystem import load_yaml, remove_dir

import pygit2
import pathlib
import os


class GitCredentials(pygit2.RemoteCallbacks):

    def __init__(self, username, password, public_key_file, private_key_file):
        self.username = username
        self.password = password
        self.public_key_file = public_key_file
        self.private_key_file = private_key_file


    def credentials(self, url, username_from_url, allowed_types):
        username = username_from_url if username_from_url else self.username

        if allowed_types & pygit2.credentials.GIT_CREDENTIAL_SSH_KEY:
            return pygit2.Keypair(
                username,
                self.public_key_file,
                self.private_key_file,
                ''
            )
        elif allowed_types & pygit2.credentials.GIT_CREDENTIAL_USERPASS_PLAINTEXT:
            return pygit2.UserPass(
                username,
                self.password
            )
        else:
            return None


class Provider(BaseProvider('module', 'git')):

    def get_module_name(self, instance):
        with temp_dir() as temp:
            temp_module_path = "{}/module".format(temp.base_path)
            repository = pygit2.clone_repository(instance.remote, temp_module_path,
                checkout_branch = instance.reference,
                callbacks = self._get_credentials(instance, temp)
            )
            config = load_yaml("{}/zimagi.yml".format(temp_module_path))

            if not isinstance(config, dict) or 'name' not in config:
                self.command.error("Module configuration required for {} at {}".format(instance.remote, instance.reference))

        return config['name']


    def initialize_instance(self, instance, created):
        super().initialize_instance(instance, created)

        remote_name = 'origin'
        with temp_dir() as temp:
            def initialize():
                module_path = self.module_path(instance.name)
                git_path = os.path.join(module_path, '.git')

                if not os.path.isdir(git_path):
                    self._init_repository(instance, temp, module_path, remote_name)
                else:
                    self._update_repository(instance, temp, module_path, remote_name)

            self.run_exclusive("git-initialize-{}".format(instance.name), initialize)

    def finalize_instance(self, instance):
        def finalize():
            module_path = self.module_path(instance.name)
            remove_dir(pathlib.Path(module_path))

        self.run_exclusive("git-finalize-{}".format(instance.name), finalize)


    def _init_repository(self, instance, temp, module_path, remote_name):
        if (os.path.exists(os.path.join(module_path, '.git'))):
            repository = pygit2.Repository(module_path)
            repository.remotes.set_url(remote_name, instance.remote)
            self._pull(instance, repository, temp, remote_name)
        else:
            repository = pygit2.clone_repository(instance.remote, module_path,
                checkout_branch = instance.reference,
                callbacks = self._get_credentials(instance, temp)
            )
        repository.update_submodules(init = True)
        self.command.success("Initialized repository from remote")

    def _update_repository(self, instance, temp, module_path, remote_name):
        try:
            repository = pygit2.Repository(module_path)
            repository.remotes.set_url(remote_name, instance.remote)

        except pygit2.GitError as e:
            remove_dir(pathlib.Path(module_path))
            return self._init_repository(instance, module_path)

        self._pull(instance, repository, temp, remote_name)
        repository.update_submodules(init = True)
        self.command.success("Updated repository from remote")


    def _pull(self, instance, repository, temp, remote_name):
        repository.checkout(repository.lookup_branch(instance.reference))

        remote = repository.remotes[remote_name]
        remote.fetch(callbacks = self._get_credentials(instance, temp))

        remote_reference = repository.lookup_reference('refs/remotes/{}/{}'.format(remote_name, instance.reference)).target
        merge_result, _ = repository.merge_analysis(remote_reference)

        if merge_result & pygit2.GIT_MERGE_ANALYSIS_UP_TO_DATE:
            return

        elif merge_result & pygit2.GIT_MERGE_ANALYSIS_FASTFORWARD:
            repository.checkout_tree(repository.get(remote_reference))
            head_reference = repository.lookup_reference('refs/heads/{}'.format(instance.reference))
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


    def _get_credentials(self, instance, temp):
        if instance.config['private_key']:
            public_key_file = temp.save(instance.config['public_key'])
            private_key_file = temp.save(instance.config['private_key'])
        else:
            public_key_file = None
            private_key_file = None

        return GitCredentials(
            instance.config['username'],
            instance.config['password'],
            public_key_file,
            private_key_file
        )
