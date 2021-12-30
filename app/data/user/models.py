from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager

from settings.roles import Roles
from systems.models.index import Model, ModelFacade
from systems.encryption.cipher import Cipher
from utility.runtime import Runtime


class UserFacade(ModelFacade('user')):

    def ensure(self, command, reinit):
        admin = self.retrieve(settings.ADMIN_USER)
        if not admin:
            original_mute = command.mute
            command.mute = True
            admin = command.user_provider.create(
                settings.ADMIN_USER, {}
            )
            command.mute = original_mute

        Runtime.admin_user(admin)


    def keep(self, key = None):
        if key:
            return []

        return settings.ADMIN_USER

    def keep_relations(self):
        return {
            'groups': {
                settings.ADMIN_USER: Roles.admin
            }
        }


    @property
    def admin(self):
        return Runtime.admin_user()

    @property
    def active_user(self):
        if not Runtime.active_user():
            self.set_active_user(self.admin)
        return Runtime.active_user()

    def set_active_user(self, user):
        Runtime.active_user(user)


class UserManager(BaseUserManager):
    use_in_migrations = True


class User(
    AbstractBaseUser,
    Model('user')
):
    USERNAME_FIELD = 'name'

    objects = UserManager()


    def save(self, *args, **kwargs):
        if not self.password and self.name == settings.ADMIN_USER:
            self.set_password(settings.DEFAULT_ADMIN_TOKEN)

        if not self.encryption_key or self.encryption_key == '<generate>':
            self.encryption_key = Cipher.get_provider_class('user_api_key').generate_key()

        super().save(*args, **kwargs)

    @property
    def env_groups(self, **filters):
        return self.groups.filter(**filters)