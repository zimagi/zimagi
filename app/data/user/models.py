from django.conf import settings
from django.db import models as django
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.utils.timezone import now, localtime

from settings.roles import Roles
from systems.models import base, resource, group, provider
from data.environment.models import Environment
from utility.runtime import Runtime

import binascii
import os


class UserFacade(
    provider.ProviderModelFacadeMixin,
    group.GroupModelFacadeMixin,
    resource.ResourceModelFacadeMixin
):
    def get_packages(self):
        return [] # Do not export with db dumps!!

    def key(self):
        return 'name'

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

    def get_provider_name(self):
        return 'user'

    def get_relations(self):
        return {
            'groups': ('group', 'Groups', '--groups')
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


    def default_order(self):
        return 'name'

    def get_list_fields(self):
        return (
            ('name', 'Username'),
            ('type', 'Type'),
            ('is_active', 'Active'),
            ('email', 'Email'),
            ('first_name', 'First name'),
            ('last_name', 'Last name')
        )

    def get_display_fields(self):
        return (
            ('name', 'Username'),
            ('type', 'Type'),
            ('first_name', 'First name'),
            ('last_name', 'Last name'),
            ('email', 'Email'),
            '---',
            ('last_login', 'Last login'),
            ('is_active', 'Active'),
            '---',
            ('created', 'Created'),
            ('updated', 'Updated')
        )

    def get_field_name_display(self, instance, value, short):
        return value

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
    resource.ResourceModel,
    AbstractBaseUser,
    metaclass = base.AppMetaModel
):
    USERNAME_FIELD = 'name'

    email = django.EmailField(null=True)
    first_name = django.CharField(max_length=30, null=True)
    last_name = django.CharField(max_length=150, null=True)
    is_active = django.BooleanField(default=True)

    objects = UserManager()

    class Meta(AbstractBaseUser.Meta):
        facade_class = UserFacade

    def get_id_fields(self):
        return ['name']

    def allowed_groups(self):
        return [ Roles.admin ]

    def save(self, *args, **kwargs):
        if not self.password and self.name == settings.ADMIN_USER:
            self.set_password(settings.DEFAULT_ADMIN_TOKEN)

        super().save(*args, **kwargs)

    @property
    def env_groups(self, **filters):
        filters['environment_id'] = Environment.facade.get_env_id()
        return self.groups.filter(**filters)