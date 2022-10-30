from django.conf import settings

from systems.plugins.index import BaseProvider
from utility.temp import temp_dir
from utility.filesystem import remove_dir
from utility.git import Git

import pathlib
import os


class Provider(BaseProvider('module', 'git')):

    remote_name = 'origin'


    def get_module_name(self, instance):
        with temp_dir() as temp:
            repository = Git.clone(instance.remote,
                "{}/module".format(temp.base_path),
                reference = instance.reference,
                **self._get_auth(instance)
            )
            config = repository.disk.load_yaml('zimagi.yml')

            if not isinstance(config, dict) or 'name' not in config:
                self.command.error("Module configuration required for {} at {}".format(
                    instance.remote,
                    instance.reference
                ))
        return config['name']


    def initialize_instance(self, instance, created):
        super().initialize_instance(instance, created)

        if not settings.DISABLE_MODULE_SYNC:
            module_path = self.module_path(instance.name)

            if not os.path.isdir(os.path.join(module_path, '.git')):
                Git.clone(instance.remote, module_path,
                    reference = instance.reference,
                    **self._get_auth(instance)
                )
                self.command.success("Initialized repository from remote")
            else:
                self.pull()
                self.command.success("Updated repository from remote")

    def finalize_instance(self, instance):
        module_path = self.module_path(instance.name)
        remove_dir(pathlib.Path(module_path))


    def _get_auth(self, instance):
        return {
            'username': instance.config['username'],
            'password': instance.secrets.get('password', None),
            'public_key': instance.secrets.get('public_key', None),
            'private_key': instance.secrets.get('private_key', None)
        }


    def init(self):
        instance = self.check_instance('git init')
        return Git.init(
            self.module_path(instance.name),
            reference = instance.reference,
            remote = self.remote_name,
            remote_url = instance.remote
        )

    def pull(self):
        instance = self.check_instance('git pull')
        repository = Git(
            self.module_path(instance.name),
            user = self.command.active_user,
            **self._get_auth(instance)
        )
        repository.set_remote(self.remote_name, instance.remote)
        return repository.pull(
            remote = self.remote_name,
            branch = instance.reference
        )

    def commit(self, message, *files):
        instance = self.check_instance('git commit')
        repository = Git(
            self.module_path(instance.name),
            user = self.command.active_user,
            **self._get_auth(instance)
        )
        return repository.commit(message, *files)

    def push(self):
        instance = self.check_instance('git push')
        repository = Git(
            self.module_path(instance.name),
            user = self.command.active_user,
            **self._get_auth(instance)
        )
        repository.set_remote(self.remote_name, instance.remote)
        return repository.push(
            remote = self.remote_name,
            branch = instance.reference
        )
