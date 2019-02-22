from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.hashers import make_password

from rest_framework.authtoken.models import Token

from systems import models

import binascii
import os


class UserFacade(models.ModelFacade):

    @property
    def admin(self):
        self.ensure()
        return getattr(self, '_admin', None)

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
        return 'username'

    def generate_token(self):
        return binascii.hexlify(os.urandom(20)).decode()


class User(AbstractUser, metaclass = models.AppMetaModel):
    
    class Meta(AbstractUser.Meta):
        facade_class = UserFacade

    @property
    def name(self):
        return self.username

    def save(self, *args, **kwargs):
        with self.facade.thread_lock:
            token = None
            try:
                token = Token.objects.get(user = self.username)
            except Exception as e:
                pass
        
            if token is None:
                if self.username == 'admin':
                    token = settings.DEFAULT_ADMIN_TOKEN
                else:
                    token = self.generate_token()
            if token:
                self.password = make_password(token)
        
            super().save(*args, **kwargs)
