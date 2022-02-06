from django.conf import settings

from settings.roles import Roles
from systems.models.index import Model, ModelFacade


class GroupFacade(ModelFacade('group')):

    def ensure(self, command, reinit):
        def initialize():
            role_provider = command.get_provider('group', settings.ROLE_PROVIDER)
            admin_role = self.retrieve(Roles.admin)

            if not admin_role:
                admin_role = role_provider.create(Roles.admin, {})
            else:
                admin_role.provider_type = settings.ROLE_PROVIDER
                admin_role.save()

            for role, description in Roles.index.items():
                if role != 'admin':
                    user_role = self.retrieve(role)
                    if not user_role:
                        user_role = role_provider.create(role)
                    else:
                        user_role.provider_type = settings.ROLE_PROVIDER

                    user_role.parent = admin_role
                    user_role.save()

            command._user.admin.groups.add(admin_role)

        command.run_exclusive('group_ensure', initialize, timeout = 0)

    def keep(self, key = None):
        if key:
            return []
        return list(Roles.index.keys())


class Group(Model('group')):

    def __str__(self):
        if self.parent and self.parent.name != self.name:
           return "{} ({})".format(self.name, self.parent)
        return self.name
