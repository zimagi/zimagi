from django.db import models as django

from systems.models import fields, environment


class StateFacade(
    environment.EnvironmentModelFacadeMixin
):
    pass


class State(
    environment.EnvironmentModel
):
    value = fields.EncryptedDataField(null = True)

    class Meta(environment.EnvironmentModel.Meta):
        verbose_name = "state"
        verbose_name_plural = "states"
        facade_class = StateFacade
