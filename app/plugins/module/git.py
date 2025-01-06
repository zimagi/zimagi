import pathlib

from django.conf import settings
from systems.plugins.index import BaseProvider
from utility.filesystem import remove_dir
from utility.git import Git
from utility.temp import temp_dir


class Provider(BaseProvider("module", "git")):
    remote_name = "origin"

    def get_module_name(self, instance):
        with temp_dir() as temp:
            repository = Git.clone(
                self.get_remote(instance),
                f"{temp.base_path}/module",
                reference=instance.reference,
                **self._get_auth(instance),
            )
            config = repository.disk.load_yaml("zimagi")

            if not isinstance(config, dict) or "name" not in config:
                self.command.error(f"Module configuration required for {self.get_remote(instance)} at {instance.reference}")
        return config["name"]

    def initialize_instance(self, instance, created):
        super().initialize_instance(instance, created)

        if not settings.DISABLE_MODULE_SYNC:
            module_path = self.module_path(instance.name)

            if not Git.check(module_path):
                Git.clone(self.get_remote(instance), module_path, reference=instance.reference, **self._get_auth(instance))
                self.command.success("Initialized repository from remote")
            else:
                self.pull()
                self.command.success("Updated repository from remote")

    def finalize_instance(self, instance):
        if not settings.DISABLE_MODULE_SYNC:
            module_path = self.module_path(instance.name)
            remove_dir(pathlib.Path(module_path))

    def _get_auth(self, instance):
        return {
            "username": instance.config["username"],
            "password": instance.secrets.get("password", None),
            "public_key": instance.secrets.get("public_key", None),
            "private_key": instance.secrets.get("private_key", None),
        }

    def init(self):
        instance = self.check_instance("git init")
        return Git.init(
            self.module_path(instance.name),
            reference=instance.reference,
            remote=self.remote_name,
            remote_url=self.get_remote(instance),
        )

    def pull(self):
        instance = self.check_instance("git pull")
        repository = Git(self.module_path(instance.name), user=self.command.active_user, **self._get_auth(instance))
        if self.command.verbosity == 3:
            self.command.info(f"Pulling updates for project {instance.name} from {self.remote_name}")

        repository.set_remote(self.remote_name, self.get_remote(instance))
        return repository.pull(remote=self.remote_name, branch=instance.reference)

    def commit(self, message, *files):
        instance = self.check_instance("git commit")
        repository = Git(self.module_path(instance.name), user=self.command.active_user, **self._get_auth(instance))
        return repository.commit(message, *files)

    def push(self):
        instance = self.check_instance("git push")
        repository = Git(self.module_path(instance.name), user=self.command.active_user, **self._get_auth(instance))
        repository.set_remote(self.remote_name, self.get_remote(instance))
        return repository.push(remote=self.remote_name, branch=instance.reference)

    def check_dirty(self):
        instance = self.check_instance("check dirty")
        repository = Git(self.module_path(instance.name))
        if repository.check_dirty():
            return True
        return False
