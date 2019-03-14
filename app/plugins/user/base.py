from systems.plugins import data


class BaseProvider(data.DataCommandProvider):

    @property
    def facade(self):
        return self.command._user
