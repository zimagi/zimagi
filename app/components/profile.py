from systems.command import profile
from utility.data import deep_merge

import copy


class ProfileComponent(profile.BaseProfileComponent):

    def priority(self):
        return 90

    def run(self, name, config, display_only = False):
        host = self.pop_value('host', config)
        profile = self.pop_value('profile', config)
        if not profile:
            self.command.error("Profile {} requires 'profile' field".format(name))

        module = self.pop_value('module', config)
        state_name = self.state_name(module, profile)
        operations = self.pop_values('operations', config)

        if display_only or not operations or 'run' in operations:
            once = self.pop_value('once', config)

            if display_only or not once or not self.command.get_state(state_name):
                self.exec('run',
                    host = host,
                    module_name = module,
                    profile_name = profile,
                    profile_config_fields = deep_merge(copy.deepcopy(self.profile.data['config']), config),
                    profile_components = self.profile.components,
                    display_only = display_only,
                    plan = self.test
                )
            self.command.set_state(state_name, True)


    def destroy(self, name, config):
        host = self.pop_value('host', config)
        profile = self.pop_value('profile', config)
        if not profile:
            self.command.error("Profile {} requires 'profile' field".format(name))

        module = self.pop_value('module', config)
        operations = self.pop_values('operations', config)

        if not operations or 'destroy' in operations:
            self.pop_value('once', config)

            self.exec('destroy',
                host = host,
                module_name = module,
                profile_name = profile,
                profile_config_fields = deep_merge(copy.deepcopy(self.profile.data['config']), config),
                profile_components = self.profile.components
            )
        self.command.delete_state(self.state_name(module, profile))


    def state_name(self, module, profile):
        return "profile-{}-{}".format(module, profile)