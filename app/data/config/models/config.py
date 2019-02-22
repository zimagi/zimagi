from systems import models
from systems.models import environment
from data.config import models as config


class ConfigFacade(
    environment.EnvironmentModelFacadeMixin,
):
    pass


class Config(
    environment.EnvironmentModel
):
    value = models.EncryptedTextField(null=True)
    groups = models.ManyToManyField(config.ConfigGroup)

    class Meta:
        facade_class = ConfigFacade

    def initialize(self, command):
        if not super().initialize(command):
            return False
        
        groups = list(self.groups.values_list('name', flat = True))
        if groups and not command.check_access(groups):
            return False
        return True
