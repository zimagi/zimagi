from django.conf import settings
from django.db import models as django
from django.contrib.auth.base_user import AbstractBaseUser

from settings import Roles
from systems.models import base, facade, group
from data.environment.models import Environment

import binascii
import os


class UserFacade(
    group.GroupModelFacadeMixin,
    facade.ModelFacade
):
    @property
    def admin(self):
        self.ensure()
        return self._admin

    @property
    def active_user(self):
        user = getattr(self, '_active_user', None)
        if not user:
            self._active_user = self.admin  
        return self._active_user

    def set_active_user(self, user):
        self._active_user = user

    def ensure(self, env = None, user = None):
        self._admin = self.retrieve(settings.ADMIN_USER)
        if not self._admin:
            self._admin, created = self.store(settings.ADMIN_USER)

    def key(self):
        return 'name'

    def generate_token(self):
        return binascii.hexlify(os.urandom(40)).decode()


class User(
    group.GroupMixin,
    AbstractBaseUser, 
    metaclass = base.AppMetaModel
):
    USERNAME_FIELD = 'name'

    name = django.CharField(primary_key=True, max_length=150)
    first_name = django.CharField(max_length=30, null=True)
    last_name = django.CharField(max_length=150, null=True)
    email = django.EmailField(null=True)
    
    class Meta(AbstractBaseUser.Meta):
        facade_class = UserFacade

    def allowed_groups(self):
        return [ Roles.admin ]

    def save(self, *args, **kwargs):
        if not self.password and self.name == settings.ADMIN_USER:
            self.set_password(settings.DEFAULT_ADMIN_TOKEN)    

        with self.facade.thread_lock:
            super().save(*args, **kwargs)

    @property
    def env_groups(self, **filters):
        filters['environment_id'] = Environment.facade.get_env()
        return self.groups.filter(**filters)