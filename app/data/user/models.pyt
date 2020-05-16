from django.conf import settings
from django.db import models as django
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.utils.timezone import now, localtime

from settings.roles import Roles
from data.state.models import State
from data import base
from data.mixins import resource, provider
from data.group import models as group
from data.environment.models import Environment
from utility.runtime import Runtime

import binascii
import os


class UserFacade(
    provider.ProviderModelFacadeMixin,
    group.GroupModelFacadeMixin,
    resource.ResourceBaseFacadeMixin
):
    def get_packages(self):
        return [] # Do not export with db dumps!!

    def ensure(self, command):
        admin = self.retrieve(settings.ADMIN_USER)
        if not admin:
            admin = command.user_provider.create(
                settings.ADMIN_USER, {}
            )
        Runtime.admin_user(admin)

    def keep(self):
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


    def get_field_email_display(self, instance, value, short):
        return value

    def get_field_first_name_display(self, instance, value, short):
        return value

    def get_field_last_name_display(self, instance, value, short):
        return value

    def get_field_is_active_display(self, instance, value, short):
        return str(value)

    def get_field_created_display(self, instance, value, short):
        return localtime(value).strftime("%Y-%m-%d %H:%M:%S %Z")

    def get_field_updated_display(self, instance, value, short):
        return localtime(value).strftime("%Y-%m-%d %H:%M:%S %Z")


class UserManager(BaseUserManager):
    use_in_migrations = True


class User(
    provider.ProviderMixin,
    group.GroupMixin,
    resource.ResourceBase,
    AbstractBaseUser,
    metaclass = base.BaseMetaModel
):
    USERNAME_FIELD = 'name'

    name = django.CharField(max_length = 254, unique = True, editable = False)

    email = django.EmailField(null = True)
    first_name = django.CharField(max_length = 30, null = True)
    last_name = django.CharField(max_length = 150, null = True)
    is_active = django.BooleanField(default = True)

    objects = UserManager()

    class Meta(AbstractBaseUser.Meta):
        verbose_name = "user"
        verbose_name_plural = "users"
        facade_class = UserFacade
        ordering = ['name']
        search_fields = []
        ordering_fields = []
        provider_name = 'user'

    def get_id(self):
        return self.name

    def allowed_groups(self):
        return [ Roles.admin ]

    def save(self, *args, **kwargs):
        if not self.password and self.name == settings.ADMIN_USER:
            self.set_password(settings.DEFAULT_ADMIN_TOKEN)

        super().save(*args, **kwargs)
        State.facade.store('group_ensure', value = True)

    @property
    def env_groups(self, **filters):
        filters['environment_id'] = Environment.facade.get_env()
        return self.groups.filter(**filters)