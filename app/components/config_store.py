from systems.commands import profile


class ProfileComponent(profile.BaseProfileComponent):

    def priority(self):
        return 0


    def run(self, name, value):
        self.exec('config save',
            config_key = name,
            config_value_type = type(value).__name__,
            config_value = value
        )
        self.profile.config.set(name, value)

    def destroy(self, name, value):
        self.exec('config remove',
            config_key = name,
            force = True
        )