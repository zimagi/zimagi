from systems.plugins import data


class BaseProvider(data.DataPluginProvider):

    @property
    def facade(self):
        return self.command._group
