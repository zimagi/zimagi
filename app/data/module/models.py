from django.conf import settings
from django.core.cache import caches

from systems.models.base import model_index
from systems.models.index import Model, ModelFacade
from utility.data import serialized_token, serialize
from utility.filesystem import load_yaml

import os
import copy


class ModuleFacade(ModelFacade('module')):

    def _ensure(self, command, reinit = False):
        if settings.DISABLE_MODULE_INIT and not reinit:
            # Module init calls ensure and we don't want to do it twice in one run
            return

        if not reinit:
            reinit = settings.CLI_EXEC and not command.get_env().runtime_image
        super()._ensure(command, reinit)

    def ensure(self, command, reinit):
        if settings.CLI_EXEC or settings.SCHEDULER_INIT:
            update_excludes = ['core']

            if not reinit:
                terminal_width = command.display_width
                command.notice(
                    "\n".join([
                        "Zimagi needs to build a container with installed module dependencies",
                        "This container will be stored and used in the future,",
                        "so this process is only needed periodically",
                        '',
                        "The requested command will run directly after this initialization",
                        "-" * terminal_width
                    ])
                )

            command.info("Updating modules from remote sources...")
            if not self.retrieve(settings.CORE_MODULE):
                command.options.add('module_provider_name', 'core')
                command.module_provider.create(settings.CORE_MODULE, {})

            for fields in self.manager.index.default_modules:
                fields = copy.deepcopy(fields)
                remote = fields.pop('remote', None)
                provider = fields.pop('provider', 'git')

                if remote:
                    command.exec_local('module add', {
                        'module_provider_name': provider,
                        'remote': remote,
                        'module_fields': fields,
                        'local': True
                    })
                elif 'name' in fields:
                    name = fields.pop('name')
                    command.exec_local('module save', {
                        'module_provider_name': provider,
                        'module_key': name,
                        'module_fields': fields,
                        'local': True
                    })
                    update_excludes.append(name)

            completed_updates = {}
            for module in command.get_instances(self):
                if module.name not in update_excludes:
                    if module.name not in completed_updates:
                        module.provider.update()

                    module.provider.load_parents(completed_updates)
                    completed_updates[module.name] = True

            command.info("Ensuring display configurations...")
            for module in command.get_instances(self):
                command.exec_local('run', {
                    'module_key': module.name,
                    'profile_key': 'display',
                    'ignore_missing': True,
                    'local': True
                })

            self.manager.ordered_modules = None
            command.exec_local('module install', {
                'verbosity': command.verbosity,
                'local': True
            })
            if not reinit:
                command.notice("-" * terminal_width)

    def keep(self, key = None):
        keep_names = []
        if key and self.manager.index.module_dependencies.get(key, None):
            keep_names = [ key ]
        elif not key:
            keep_names = [ settings.CORE_MODULE ] + self.manager.index.get_default_module_names()
        return keep_names


    def delete(self, key, **filters):
        result = super().delete(key, **filters)
        if result:
            self.model.save_deploy_modules()
        return result

    def clear(self, **filters):
        result = super().clear(**filters)
        if result:
            self.model.save_deploy_modules()
        return result


    def get_field_status_display(self, instance, value, short):
        if value == self.model.STATUS_VALID:
            return self.success_color(value)
        return self.error_color(value)


class Module(Model('module')):

    STATUS_VALID = 'valid'
    STATUS_INVALID = 'invalid'


    @property
    def status(self):
        zimagi_path = self._get_config_file()
        if (self.name == 'core' or os.path.isfile(zimagi_path)) and self.provider.check_module():
            return self.STATUS_VALID
        return self.STATUS_INVALID

    @property
    def version(self):
        if self.name == 'core':
            return settings.VERSION
        return self._load_config().get('version', None)

    @property
    def compatibility(self):
        if self.name == 'core':
            return settings.VERSION
        return self._load_config().get('compatibility', None)


    def save(self, *args, **kwargs):
        try:
            caches[settings.CACHE_MIDDLEWARE_ALIAS].clear()
            caches[settings.CACHE_MIDDLEWARE_ALIAS].close()
        except Exception:
            pass

        super().save(*args, **kwargs)
        self.save_deploy_modules()


    @classmethod
    def save_deploy_modules(cls):
        config_facade = model_index().get_facade_index()['config']
        deploy_modules = []
        for module in cls.facade.all():
            if module.remote:
                deploy_modules.append({
                    'remote': module.remote,
                    'reference': module.reference,
                    'config': module.config
                })
        config_facade.store('deploy_modules', {
            'value': serialized_token() + serialize(deploy_modules),
            'value_type': 'str',
            'provider_type': 'base'
        })


    def _get_config_file(self):
        path = self.provider.module_path(self.name, ensure = False)
        return os.path.join(path, 'zimagi.yml')

    def _load_config(self):
        if not getattr(self, '_config_data', None):
            zimagi_path = self._get_config_file()
            self._config_data = load_yaml(zimagi_path) if os.path.isfile(zimagi_path) else {}
        return self._config_data
