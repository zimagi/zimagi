from settings.roles import Roles
from systems.models.index import ModelMixin, ModelMixinFacade
from data.group.cache import Cache

import threading


class GroupMixinFacadeOverride(ModelMixinFacade('group')):

    def check_group_access(self, instance, command):
        if not command.check_access(instance):
            return False
        return True


class GroupMixinOverride(ModelMixin('group')):

    group_lock = threading.Lock()


    def access_groups(self, reset = False):
        return self.allowed_groups() + self.group_names(reset)

    def allowed_groups(self):
        return [ Roles.admin ]

    def group_names(self, reset = False):
        with self.group_lock:
            # This can still get wonky somehow with heavy parallelism
            return Cache().get(self.facade, self.id,
                reset = reset
            )


    def save(self, *args, **kwargs):
        Cache().clear(self.facade)
        super().save(*args, **kwargs)


    def initialize(self, command):
        if getattr(super(), 'initialize', None):
            if not super().initialize(command):
                return False
        return self.facade.check_group_access(self, command)
