from requests.exceptions import ConnectTimeout, ConnectionError

from systems.commands import profile
from utility.data import deep_merge

import copy


class ProfileComponent(profile.BaseProfileComponent):

    def priority(self):
        return 90

    def ensure_module_config(self):
        return True


    def run(self, name, config, display_only = False):
        host = self.pop_value('host', config)
        profile = self.pop_value('profile', config)
        if not profile:
            self.command.error("Profile {} requires 'profile' field".format(name))

        module = self.pop_value('module', config)
        state_name = self.state_name(module, profile)
        operations = self.pop_values('operations', config)

        components = self.pop_values('components', config)
        if self.profile.components and components:
            components = list(set(self.profile.components) & set(components))
        elif self.profile.components:
            components = self.profile.components

        if display_only or not operations or 'run' in operations:
            once = self.pop_value('once', config)

            if display_only or not once or not self.command.get_state(state_name):
                run_options = {
                    "environment_host": host,
                    "module_name": module,
                    "profile_name": profile,
                    "profile_config_fields": deep_merge(copy.deepcopy(self.profile.data['config']), config),
                    "profile_components": components,
                    "display_only": display_only,
                    "plan": self.test
                }
                try:
                    self.exec('run', **run_options)

                except (ConnectTimeout, ConnectionError) as e:
                    if display_only:
                        run_options.pop('environment_host', None)
                        self.command.warning("Displaying local profile for: {}\n".format(name))
                        self.exec('run', **run_options)
                    else:
                        raise e

            self.command.set_state(state_name, True)


    def destroy(self, name, config):
        host = self.pop_value('host', config)
        profile = self.pop_value('profile', config)
        if not profile:
            self.command.error("Profile {} requires 'profile' field".format(name))

        module = self.pop_value('module', config)
        operations = self.pop_values('operations', config)

        components = self.pop_values('components', config)
        if self.profile.components and components:
            components = list(set(self.profile.components) & set(components))
        elif self.profile.components:
            components = self.profile.components

        if not operations or 'destroy' in operations:
            self.pop_value('once', config)

            try:
                self.exec('destroy',
                    environment_host = host,
                    module_name = module,
                    profile_name = profile,
                    profile_config_fields = deep_merge(copy.deepcopy(self.profile.data['config']), config),
                    profile_components = components
                )
            except (ConnectTimeout, ConnectionError):
                self.command.warning("Remote host does not exist for: {}".format(name))

        self.command.delete_state(self.state_name(module, profile))


    def state_name(self, module, profile):
        return "profile-{}-{}".format(module, profile)