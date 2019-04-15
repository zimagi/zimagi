from systems.command import profile
from systems.command.parsers.config import ConfigParser


class Provisioner(profile.BaseProvisioner):

    def priority(self):
        return 0

    def ensure(self, name, value):
        self.exec('config save',
            config_name = name,
            config_value_type = type(value).__name__,
            config_value = value
        )
        ConfigParser.runtime_variables[name] = value

    def destroy(self, name, value):
        self.exec('config rm',
            config_name = name,
            force = True
        )