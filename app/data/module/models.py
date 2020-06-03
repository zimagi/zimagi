from django.conf import settings
from django.core.cache import caches

from systems.models.index import Model, ModelFacade

import os


class ModuleFacade(ModelFacade('module')):

    def _ensure(self, command, reinit = False):
        if settings.DISABLE_MODULE_INIT or (command.get_full_name() == 'module init' and not reinit):
            # Module init calls ensure and we don't want to do it twice in one run
            return

        if not reinit:
            reinit = settings.CLI_EXEC and not command.get_env().runtime_image
        super()._ensure(command, reinit)

    def ensure(self, command, reinit):
        terminal_width = command.display_width

        if not reinit:
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
            command.options.add('module_provider_name', 'sys_internal')
            command.module_provider.create(settings.CORE_MODULE, {})

        for name, fields in self.manager.index.default_modules.items():
            provider = fields.pop('provider', 'git')
            command.exec_local('module save', {
                'module_provider_name': provider,
                'module_name': name,
                'module_fields': fields
            })

        for module in command.get_instances(self):
            module.provider.update()
            module.provider.load_parents()

        command.info("Ensuring display configurations...")
        for module in command.get_instances(self):
            command.exec_local('run', {
                'module_name': module.name,
                'profile_name': 'display',
                'ignore_missing': True
            })

        self.manager.ordered_modules = None
        command.exec_local('module install', {
            'verbosity': command.verbosity
        })
        if not reinit:
            command.notice("-" * terminal_width)

    def keep(self):
        return [ settings.CORE_MODULE ] + list(self.manager.index.default_modules.keys())


    def get_field_status_display(self, instance, value, short):
        if value == self.model.STATUS_VALID:
            return self.success_color(value)
        return self.error_color(value)


class Module(Model('module')):

    STATUS_VALID = 'valid'
    STATUS_INVALID = 'invalid'


    @property
    def status(self):
        path = self.provider.module_path(self.name, ensure = False)
        zimagi_path = os.path.join(path, 'zimagi.yml')

        if os.path.isfile(zimagi_path):
            return self.STATUS_VALID
        return self.STATUS_INVALID


    def save(self, *args, **kwargs):
        caches['api'].clear()
        caches['api'].close()
        super().save(*args, **kwargs)
