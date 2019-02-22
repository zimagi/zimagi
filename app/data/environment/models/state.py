from systems import models
from systems.models import environment


class StateFacade(
    environment.EnvironmentModelFacadeMixin
):
    pass


class State(
    environment.EnvironmentModel
):
    value = models.EncryptedTextField(null=True)
    
    class Meta:
        facade_class = StateFacade
