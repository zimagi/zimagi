from django.conf import settings
from django.db import models as django
from django.contrib.auth.base_user import AbstractBaseUser
from django.utils.timezone import now

from settings import Roles
from systems.models import base, facade, group, provider
from data.environment.models import Environment

import binascii
import os


class UserFacade(
    provider.ProviderModelFacadeMixin,
    group.GroupModelFacadeMixin,
    facade.ModelFacade
):
    def key(self):
        return 'name'

    def ensure(self, command):
        self._admin = self.retrieve(settings.ADMIN_USER)
        if not self._admin:
            self._admin = command.user_provider.create(
                settings.ADMIN_USER, {}
            )

    def get_provider_name(self):
        return 'user'


    @property
    def admin(self):
        return self._admin

    @property
    def active_user(self):
        user = getattr(self, '_active_user', None)
        if not user:
            self._active_user = self.admin  
        return self._active_user

    def set_active_user(self, user):
        self._active_user = user

    def generate_token(self):
        return binascii.hexlify(os.urandom(40)).decode()


class User(
    provider.ProviderMixin,
    group.GroupMixin,
    AbstractBaseUser, 
    metaclass = base.AppMetaModel
):
    USERNAME_FIELD = 'name'

    name = django.CharField(primary_key=True, max_length=150)
    email = django.EmailField(null=True)
    first_name = django.CharField(max_length=30, null=True)
    last_name = django.CharField(max_length=150, null=True)
    is_active = django.BooleanField(default=True)
    created = django.DateTimeField(null=True)    
    updated = django.DateTimeField(null=True)
        
    class Meta(AbstractBaseUser.Meta):
        facade_class = UserFacade

    def allowed_groups(self):
        return [ Roles.admin ]

    def save(self, *args, **kwargs):
        if not self.password and self.name == settings.ADMIN_USER:
            self.set_password(settings.DEFAULT_ADMIN_TOKEN)

        if self.created is None:
            self.created = now()
        else:
            self.updated = now()   

        with self.facade.thread_lock:
            super().save(*args, **kwargs)

    @property
    def env_groups(self, **filters):
        filters['environment_id'] = Environment.facade.get_env()
        return self.groups.filter(**filters)