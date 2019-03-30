from systems.command import profile


class Provisioner(profile.BaseProvisioner):

    def priority(self):
        return 0

    def ensure(self, name, value):
        self.exec('config save',
            config_name = name,
            config_value_type = type(value).__name__,
            config_value = value
        )

    def destroy(self, name, value):
        self.exec('config rm',
            config_name = name,
            force = True
        )
