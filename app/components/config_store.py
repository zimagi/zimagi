from systems.command import profile
from systems.command.parsers.config import ConfigParser


class ProfileComponent(profile.BaseProfileComponent):

    def priority(self):
        return 0

    def run(self, name, value):
        self.exec('config save',
            config_name = name,
            config_value_type = type(value).__name__,
            config_value = value,
            local = self.command.local
        )
        ConfigParser.runtime_variables[name] = value

    def destroy(self, name, value):
        self.exec('config rm',
            config_name = name,
            local = self.command.local,
            force = True
        )