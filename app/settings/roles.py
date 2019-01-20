
class RoleAccessError(Exception):
    pass


class MetaRoles(type):
    
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
    index = {
        # Environment roles
        'admin': "Core administrator (full privileges over all systems)",
        'config-admin': "Configuration administrator (full privileges over environment configurations)",
        'db-admin': "Database administrator (full privileges over database operations)",
        
        # User roles
        'user-admin': "User administrator (full privileges over system users, groups, and tokens)",
        'user-group-admin': "User group administrator (full privileges over system user groups)",
        
        # Project roles
        'project-admin': "Project administrator (full privileges over all environment projects)",
        
        # Server roles
        'server-admin': "Server administrator (full privileges over all environment servers)",
        'server-group-admin': "Server group administrator (full privileges over environment server groups)",
        
        # Storage roles
        'storage-admin': "Storage administrator (full privileges over all environment storage mounts)"
    }
