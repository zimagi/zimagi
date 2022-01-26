from requests.exceptions import ConnectTimeout, ConnectionError
from django.conf import settings

from systems.commands import profile
from utility.data import deep_merge

import copy


class ProfileComponent(profile.BaseProfileComponent):

    def priority(self):
        return 40

    def ensure_module_config(self):
        return True


    def run(self, name, config, display_only = False):
        config = copy.deepcopy(config)
        host = self.pop_value('_host', config)

        profile = self.pop_value('_profile', config)
        if not profile:
            self.command.error("Profile {} requires '_profile' field".format(name))

        queue = self.pop_value('_queue', config) if '_queue' in config else settings.QUEUE_COMMANDS
        module = self.pop_value('_module', config)
        state_name = self.state_name(module, profile)
        operations = self.pop_values('_operations', config)
        wait_keys = self.pop_values('_wait_keys', config)
        log_key = None

        components = self.pop_values('_components', config)
        if self.profile.components and components:
            components = list(set(self.profile.components) & set(components))
        elif self.profile.components:
            components = self.profile.components

        if display_only or not operations or 'run' in operations:
            once = self.pop_value('_once', config)

            if display_only or not once or not self.command.get_state(state_name):
                options = {
                    "environment_host": host,
                    "module_name": module,
                    "profile_name": profile,
                    "profile_config_fields": deep_merge(copy.deepcopy(self.profile.data['config']), config),
                    "profile_components": components,
                    "display_only": display_only,
                    "test": self.test,
                    '_wait_keys': wait_keys
                }
                if settings.QUEUE_COMMANDS:
                    options['push_queue'] = queue if not display_only else False
                try:
                    log_key = self.exec('run', **options)

                except (ConnectTimeout, ConnectionError) as e:
                    if display_only:
                        options.pop('environment_host', None)
                        options.pop('push_queue', None)
                        self.command.warning("Displaying local profile for: {}\n".format(name))
                        log_key = self.exec('run', **options)
                    else:
                        raise e

            self.command.set_state(state_name, True)
        return log_key if queue else None


    def destroy(self, name, config, display_only = False):
        config = copy.deepcopy(config)
        host = self.pop_value('_host', config)
        profile = self.pop_value('_profile', config)
        if not profile:
            self.command.error("Profile {} requires '_profile' field".format(name))

        queue = self.pop_value('_queue', config) if '_queue' in config else settings.QUEUE_COMMANDS
        module = self.pop_value('_module', config)
        operations = self.pop_values('_operations', config)
        wait_keys = self.pop_values('_wait_keys', config)
        log_key = None

        components = self.pop_values('_components', config)
        if self.profile.components and components:
            components = list(set(self.profile.components) & set(components))
        elif self.profile.components:
            components = self.profile.components

        if not operations or 'destroy' in operations:
            self.pop_value('_once', config)

            options = {
                "environment_host": host,
                "module_name": module,
                "profile_name": profile,
                "profile_config_fields": deep_merge(copy.deepcopy(self.profile.data['config']), config),
                "profile_components": components,
                "display_only": display_only,
                "_wait_keys": wait_keys
            }
            if settings.QUEUE_COMMANDS:
                options['push_queue'] = queue if not display_only else False
            try:
                log_key = self.exec('destroy', **options)

            except (ConnectTimeout, ConnectionError):
                self.command.warning("Remote host does not exist for: {}".format(name))

        self.command.delete_state(self.state_name(module, profile))
        return log_key if queue else None


    def state_name(self, module, profile):
        return "profile-{}-{}".format(module, profile)
