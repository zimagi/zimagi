from systems.commands import profile
from plugins.parser.config import Provider as ConfigParser


class ProfileComponent(profile.BaseProfileComponent):

    def priority(self):
        return 0

    def skip_describe(self):
        return True


    def run(self, name, value):
        self.exec('config save',
            config_name = name,
            config_value_type = type(value).__name__,
            config_value = value
        )
        ConfigParser.runtime_variables[name] = value

    def destroy(self, name, value):
        self.exec('config remove',
            config_name = name,
            force = True
        )