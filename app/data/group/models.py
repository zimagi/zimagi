from settings.roles import Roles
from systems.models.index import Model, ModelFacade


class GroupFacade(ModelFacade('group')):

    def ensure(self, command, reinit):
        admin_group = self.retrieve(Roles.admin)
        if not admin_group:
            admin_group = command.group_provider.create(Roles.admin, {})

        for role, description in Roles.index.items():
            if role != 'admin':
                group = self.retrieve(role)
                if not group:
                    group = command.group_provider.create(role)
                    group.parent = admin_group
                    group.save()

        command._user.admin.groups.add(admin_group)

    def keep(self, key = None):
        if key:
            return []
        return list(Roles.index.keys())


class Group(Model('group')):

    def __str__(self):
        if self.parent:
            return "{} ({})".format(self.name, self.parent)
        return self.name
