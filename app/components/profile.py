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
        host = self.pop_value('_host', config)
        profile = self.pop_value('_profile', config)
        if not profile:
            self.command.error("Profile {} requires '_profile' field".format(name))

        queue = self.pop_value('_queue', config) if '_queue' in config else settings.QUEUE_COMMANDS
        reverse_status = self.pop_value('_reverse_status', config)
        module = self.pop_value('_module', config)
        state_name = self.state_name(module, profile)
        operations = self.pop_values('_operations', config)
        wait_keys = self.pop_values('_wait_keys', config)

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
                    "module_key": module,
                    "profile_key": profile,
                    "profile_config_fields": deep_merge(copy.deepcopy(self.profile.data['config']), config),
                    "profile_components": components,
                    "display_only": display_only,
                    '_wait_keys': wait_keys
                }
                if settings.QUEUE_COMMANDS:
                    options['push_queue'] = queue if not display_only else False
                if reverse_status is True or reverse_status == 'run':
                    options['reverse_status'] = True
                try:
                    self.exec(name, 'run', **options)

                except (ConnectTimeout, ConnectionError) as e:
                    if display_only:
                        options.pop('environment_host', None)
                        options.pop('push_queue', None)
                        self.command.warning("Displaying local profile for: {}\n".format(name))
                        self.exec(name, 'run', **options)
                    else:
                        raise e

            self.command.set_state(state_name, True)


    def destroy(self, name, config, display_only = False):
        host = self.pop_value('_host', config)
        profile = self.pop_value('_profile', config)
        if not profile:
            self.command.error("Profile {} requires '_profile' field".format(name))

        queue = self.pop_value('_queue', config) if '_queue' in config else settings.QUEUE_COMMANDS
        reverse_status = self.pop_value('_reverse_status', config)
        module = self.pop_value('_module', config)
        operations = self.pop_values('_operations', config)
        wait_keys = self.pop_values('_wait_keys', config)

        components = self.pop_values('_components', config)
        if self.profile.components and components:
            components = list(set(self.profile.components) & set(components))
        elif self.profile.components:
            components = self.profile.components

        if not operations or 'destroy' in operations:
            self.pop_value('_once', config)

            options = {
                "environment_host": host,
                "module_key": module,
                "profile_key": profile,
                "profile_config_fields": deep_merge(copy.deepcopy(self.profile.data['config']), config),
                "profile_components": components,
                "display_only": display_only,
                "_wait_keys": wait_keys
            }
            if settings.QUEUE_COMMANDS:
                options['push_queue'] = queue if not display_only else False
            if reverse_status is True or reverse_status == 'destroy':
                options['reverse_status'] = True
            try:
                self.exec(name, 'destroy', **options)

            except (ConnectTimeout, ConnectionError):
                self.command.warning("Remote host does not exist for: {}".format(name))

        self.command.delete_state(self.state_name(module, profile))


    def state_name(self, module, profile):
        return "profile-{}-{}".format(module, profile)
