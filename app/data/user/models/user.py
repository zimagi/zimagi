
from django.db import models
from django.contrib.auth.models import AbstractUser

from systems import models


class UserFacade(models.ModelFacade):

    def key(self):
        return 'username'


class User(AbstractUser, metaclass = models.AppMetaModel):
    
    class Meta(AbstractUser.Meta):
        facade_class = UserFacade
