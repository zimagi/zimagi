from django.conf import settings


class RoleAccessError(Exception):
    pass


class MetaRoles(type):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.index = settings.LOADER.load_roles()


    def __getattr__(self, name):
        name = name.replace('_', '-')

        if name in self.index:
            return name
        else:
            raise RoleAccessError("Role {} does not exist".format(name))


    def get_index(self):
        return self.index

    def get_help(self, name):
        return self.index[name]


class Roles(object, metaclass = MetaRoles):
    pass

