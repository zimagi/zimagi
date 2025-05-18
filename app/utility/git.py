import os
import re

import pygit2
from django.conf import settings

from .filesystem import FileSystem
from .temp import temp_dir


class GitError(Exception):
    pass


class GitCredentials(pygit2.RemoteCallbacks):
    def __init__(self, username, password, public_key_file, private_key_file):
        self.username = username
        self.password = password
        self.public_key_file = public_key_file
        self.private_key_file = private_key_file

    def credentials(self, url, username_from_url, allowed_types):
        username = username_from_url if username_from_url else self.username

        if allowed_types & pygit2.enums.CredentialType.SSH_KEY:
            return pygit2.Keypair(username, self.public_key_file, self.private_key_file, "")
        elif allowed_types & pygit2.enums.CredentialType.USERNAME:
            return pygit2.UserPass(username, self.password)
        else:
            return None


class Git:
    DEFAULT_USER = "git"
    DEFAULT_REMOTE = "origin"
    DEFAULT_BRANCH = "main"

    @classmethod
    def check(cls, directory):
        if os.path.isdir(os.path.join(directory, ".git")):
            return True
        return False

    @classmethod
    def clone(cls, remote_url, path, reference=DEFAULT_BRANCH, **auth_options):
        user_match = re.match(r"^(?:https?://|ssh://)?([^\@]+)\@.+", remote_url)
        if user_match:
            auth_options["username"] = user_match.group(1)

        with temp_dir() as temp:
            repository = cls(
                pygit2.clone_repository(
                    remote_url, path, checkout_branch=reference, callbacks=cls._get_credentials(temp, **auth_options)
                ),
                **auth_options,
            )
        return repository

    @classmethod
    def init(cls, path, reference=DEFAULT_BRANCH, remote=DEFAULT_REMOTE, remote_url=None):
        repository = pygit2.init_repository(path, bare=False, initial_head=reference)
        if remote and remote_url:
            repository.remotes.set_url(remote, remote_url)
            repository.config.set_multivar(
                f"remote.{remote}.fetch", "", f"+refs/heads/{reference}:refs/remotes/{remote}/{reference}"
            )
        return cls(repository, reference=reference)

    @classmethod
    def _get_credentials(cls, temp, username=DEFAULT_USER, password=None, public_key=None, private_key=None):
        return GitCredentials(
            username,
            password,
            temp.save(public_key) if public_key else None,
            temp.save(private_key) if private_key else None,
        )

    def __init__(self, repo_reference, reference=DEFAULT_BRANCH, user=None, **auth_options):
        if isinstance(repo_reference, pygit2.Repository):
            self.repository = repo_reference
        else:
            self.repository = pygit2.Repository(repo_reference)

        self.disk = FileSystem(self.repository.workdir)
        self._default_reference = reference

        self.user = None
        if user:
            self.set_user(user)

        self.auth_options = {}
        if auth_options:
            self.set_auth(**auth_options)

        self.repository.submodules.update(init=True)

    @property
    def reference(self):
        try:
            return self.repository.head.shorthand
        except pygit2.errors.GitError:
            return self._default_reference

    def set_user(self, user):
        self.user = pygit2.Signature(
            f"{user.first_name} {user.last_name}" if user.first_name and user.last_name else user.name,
            user.email if user.email else f"{user.name}@{settings.APP_NAME}",
        )

    def get_remote(self, remote=DEFAULT_REMOTE):
        return self.repository.remotes[remote]

    def set_remote(self, remote, remote_url):
        self.repository.remotes.set_url(remote, remote_url)

        user_match = re.match(r"^(?:https?://|ssh://)?([^\@]+)\@.+", remote_url)
        if user_match:
            self.auth_options["username"] = user_match.group(1)

    def set_auth(self, **auth_options):
        for name, value in auth_options.items():
            self.auth_options[name] = value

    def checkout(self, branch):
        self.repository.checkout(self.repository.lookup_branch(branch))

    def pull(self, remote=DEFAULT_REMOTE, branch=None):
        branch = self.reference if not branch else branch
        if branch != self.reference:
            self.checkout(branch)

        remote_obj = self.get_remote(remote)
        with temp_dir() as temp:
            remote_obj.fetch(callbacks=self._get_credentials(temp, **self.auth_options))

        remote_reference = self.repository.lookup_reference(f"refs/remotes/{remote}/{branch}").target
        merge_result, _ = self.repository.merge_analysis(remote_reference)

        if merge_result & pygit2.GIT_MERGE_ANALYSIS_UP_TO_DATE:
            return

        elif merge_result & pygit2.GIT_MERGE_ANALYSIS_FASTFORWARD:
            self.repository.checkout_tree(self.repository.get(remote_reference))
            head_reference = self.repository.lookup_reference(f"refs/heads/{branch}")
            head_reference.set_target(remote_reference)
            self.repository.head.set_target(remote_reference)

        elif merge_result & pygit2.GIT_MERGE_ANALYSIS_NORMAL:
            self.repository.merge(remote_reference)

            tree = self.repository.index.write_tree()
            self.repository.create_commit(
                "HEAD", self.user, self.user, "Merge", tree, [self.repository.head.target, remote_reference]
            )
            self.repository.state_cleanup()
            self.repository.update_submodules(init=True)
        else:
            raise GitError(f"Unable to pull {branch} changes from remote {remote}")

    def commit(self, message, *files):
        if files:
            for file in files:
                self.repository.index.add(file)
        else:
            self.repository.index.add_all()

        self.repository.index.write()

        try:
            parents = [self.repository.head.target]
        except pygit2.errors.GitError:
            parents = []

        self.repository.create_commit(
            f"refs/heads/{self.reference}", self.user, self.user, message, self.repository.index.write_tree(), parents
        )

    def push(self, remote=DEFAULT_REMOTE, branch=None):
        branch = self.reference if not branch else branch
        if branch != self.reference:
            self.checkout(branch)

        remote_obj = self.get_remote(remote)
        with temp_dir() as temp:
            remote_obj.push([f"refs/heads/{branch}"], callbacks=self._get_credentials(temp, **self.auth_options))

    def check_dirty(self):
        return self.repository.status()
