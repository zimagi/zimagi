from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.hashers import make_password

from rest_framework.authtoken.models import Token

from systems import models

import binascii
import os


class UserFacade(models.ModelFacade):

    def get_packages(self):
        return super().get_packages() + ['user']


    @property
    def admin(self):
        return getattr(self, '_admin', None)

    @property
    def active_user(self):
        return getattr(self, '_active_user', None)

    def set_active_user(self, user):
        self._active_user = user


    def ensure(self, env, user):
        admin = self.retrieve(settings.ADMIN_USER)

        if not admin:
            self.store(settings.ADMIN_USER)


    def key(self):
        return 'username'

    def store(self, key, **values):
        user = self.retrieve(key)
        
        if user:
            token = Token.objects.get(user = user)
        else:
            if key == 'admin':
                token = settings.DEFAULT_ADMIN_TOKEN
            else:
                token = self.generate_token()

        values['password'] = make_password(token)

        instance, created = super().store(key, **values)

        if not user:
            Token.objects.create(user = instance, key = token)

        return (instance, created)


    def generate_token(self):
        return binascii.hexlify(os.urandom(20)).decode()


class User(AbstractUser, metaclass = models.AppMetaModel):
    
    class Meta(AbstractUser.Meta):
        facade_class = UserFacade
