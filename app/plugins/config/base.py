from systems.command.providers import data


class BaseProvider(data.DataCommandProvider):

    @property
    def facade(self):
        return self.command._config
