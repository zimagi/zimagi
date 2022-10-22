from django.conf import settings

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

    remote_name = 'origin'


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

        if not settings.DISABLE_MODULE_SYNC:
            git_path = os.path.join(
                self.module_path(instance.name),
                '.git'
            )
            if not os.path.isdir(git_path):
                self._init_repository(instance)
            else:
                self._update_repository(instance)

    def finalize_instance(self, instance):
        module_path = self.module_path(instance.name)
        remove_dir(pathlib.Path(module_path))


    def init(self):
        instance = self.check_instance('git init')
        repository = pygit2.init_repository(
            self.module_path(instance.name),
            bare = False,
            initial_head = instance.reference
        )
        repository.remotes.set_url(self.remote_name, instance.remote)
        repository.config.set_multivar(
            "remote.{}.fetch".format(self.remote_name),
            '',
            "+refs/heads/{}:refs/remotes/{}/{}".format(
                instance.reference,
                self.remote_name,
                instance.reference
            )
        )

    def pull(self):
        instance = self.check_instance('git pull')
        repository = pygit2.Repository(self.module_path(instance.name))
        repository.remotes.set_url(self.remote_name, instance.remote)

        repository.checkout(repository.lookup_branch(instance.reference))

        with temp_dir() as temp:
            remote = repository.remotes[self.remote_name]
            remote.fetch(callbacks = self._get_credentials(instance, temp))

        remote_reference = repository.lookup_reference(
            'refs/remotes/{}/{}'.format(self.remote_name, instance.reference)
        ).target
        merge_result, _ = repository.merge_analysis(remote_reference)

        if merge_result & pygit2.GIT_MERGE_ANALYSIS_UP_TO_DATE:
            return

        elif merge_result & pygit2.GIT_MERGE_ANALYSIS_FASTFORWARD:
            repository.checkout_tree(repository.get(remote_reference))
            head_reference = repository.lookup_reference('refs/heads/{}'.format(instance.reference))
            head_reference.set_target(remote_reference)
            repository.head.set_target(remote_reference)

        elif merge_result & pygit2.GIT_MERGE_ANALYSIS_NORMAL:
            user = self.command.active_user

            repository.merge(remote_reference)
            committer = pygit2.Signature(
                "{} {}".format(user.first_name, user.last_name) if user.first_name and user.last_name else user.name,
                user.email if user.email else "{}@{}".format(user.name, settings.APP_NAME)
            )
            tree = repository.index.write_tree()
            repository.create_commit('HEAD',
                committer, committer, 'Merge',
                tree,
                [ repository.head.target, remote_reference ]
            )
            repository.state_cleanup()
        else:
            self.command.error("Unable to pull remote changes from remote")

    def commit(self, message, *files):
        instance = self.check_instance('git commit')
        repository = pygit2.Repository(self.module_path(instance.name))
        user = self.command.active_user

        if files:
            for file in files:
                repository.index.add(file)
        else:
            repository.index.add_all()

        repository.index.write()

        committer = pygit2.Signature(
            "{} {}".format(user.first_name, user.last_name) if user.first_name and user.last_name else user.name,
            user.email if user.email else "{}@{}".format(user.name, settings.APP_NAME)
        )

        try:
            parents = [ repository.head.target ]
        except pygit2.errors.GitError:
            parents = []

        repository.create_commit(
            "refs/heads/{}".format(instance.reference),
            committer, committer, message,
            repository.index.write_tree(),
            parents
        )

    def push(self):
        instance = self.check_instance('git push')
        repository = pygit2.Repository(self.module_path(instance.name))
        repository.remotes.set_url(self.remote_name, instance.remote)

        with temp_dir() as temp:
            remote = repository.remotes[self.remote_name]
            remote.push([ "refs/heads/{}".format(instance.reference) ],
                callbacks = self._get_credentials(instance, temp)
            )


    def _init_repository(self, instance):
        module_path = self.module_path(instance.name)

        if (os.path.exists(os.path.join(module_path, '.git'))):
            repository = pygit2.Repository(module_path)
            repository.remotes.set_url(self.remote_name, instance.remote)
            self.pull()
        else:
            with temp_dir() as temp:
                repository = pygit2.clone_repository(instance.remote, module_path,
                    checkout_branch = instance.reference,
                    callbacks = self._get_credentials(instance, temp)
                )
        repository.update_submodules(init = True)
        self.command.success("Initialized repository from remote")

    def _update_repository(self, instance):
        module_path = self.module_path(instance.name)
        try:
            repository = pygit2.Repository(module_path)
            repository.remotes.set_url(self.remote_name, instance.remote)

        except pygit2.GitError as e:
            remove_dir(pathlib.Path(module_path))
            return self._init_repository(instance)

        self.pull()
        repository.update_submodules(init = True)
        self.command.success("Updated repository from remote")


    def _get_credentials(self, instance, temp):
        if instance.secrets.get('private_key', None):
            public_key_file = temp.save(instance.secrets['public_key'])
            private_key_file = temp.save(instance.secrets['private_key'])
        else:
            public_key_file = None
            private_key_file = None

        return GitCredentials(
            instance.config['username'],
            instance.secrets.get('password', None),
            public_key_file,
            private_key_file
        )
