
from django.db import models
from rest_framework.authtoken import models as token_models

from systems import models


class TokenFacade(models.ModelFacade):
    pass


class Token(token_models.Token, metaclass = models.AppMetaModel):

    class Meta:
        proxy = True
        facade_class = TokenFacade
