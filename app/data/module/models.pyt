from django.conf import settings
from django.db import models as django
from django.core.cache import caches

from settings.roles import Roles
from data.state.models import State
from data.environment import models as environment
from data.group import models as group
from data.mixins import provider
from utility.runtime import Runtime

import os


class ModuleFacade(
    provider.ProviderModelFacadeMixin,
    group.GroupModelFacadeMixin,
    environment.EnvironmentBaseFacadeMixin
):
    def ensure(self, command, reinit = False):
        if settings.DISABLE_MODULE_INIT or (command.get_full_name() == 'module init' and not reinit):
            # Module init calls ensure and we don't want to do it twice in one run
            return

        if reinit or command.get_state('module_ensure', True) or \
            (settings.CLI_EXEC and not command.get_env().runtime_image):

            terminal_width = command.display_width

            if not reinit:
                command.notice(
                    "\n".join([
                        "MCMI needs to build a container with installed module dependencies",
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

            for name, fields in self.manager.default_modules.items():
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
            command.set_state('module_ensure', False)

            if not reinit:
                command.notice("-" * terminal_width)

    def keep(self):
        return [ settings.CORE_MODULE ] + list(self.manager.default_modules.keys())

    def get_field_remote_display(self, instance, value, short):
        return value

    def get_field_reference_display(self, instance, value, short):
        return value

    def get_field_status_display(self, instance, value, short):
        if value == self.model.STATUS_VALID:
            return self.success_color(value)
        return self.error_color(value)


class Module(
    provider.ProviderMixin,
    group.GroupMixin,
    environment.EnvironmentBase
):
    STATUS_VALID = 'valid'
    STATUS_INVALID = 'invalid'

    remote = django.CharField(null = True, max_length = 256)
    reference = django.CharField(null = True, max_length = 128)

    class Meta(environment.EnvironmentBase.Meta):
        verbose_name = "module"
        verbose_name_plural = "modules"
        facade_class = ModuleFacade
        dynamic_fields = ['status']
        ordering = ['-provider_type', 'name']
        provider_name = 'module'

    @property
    def status(self):
        path = self.provider.module_path(self.name, ensure = False)
        mcmi_path = os.path.join(path, 'mcmi.yml')

        if os.path.isfile(mcmi_path):
            return self.STATUS_VALID
        return self.STATUS_INVALID


    def allowed_groups(self):
        return [ Roles.admin, Roles.module_admin ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        State.facade.store('module_ensure', value = True)
        State.facade.store('group_ensure', value = True)
        State.facade.store('config_ensure', value = True)

        caches['api'].clear()
        caches['api'].close()
