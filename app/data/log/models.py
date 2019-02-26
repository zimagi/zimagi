from django.db import models as django
from django.utils.timezone import now

from systems.models import fields, environment, config
from data.user.models import User


class LogFacade(
    config.ConfigModelFacadeMixin,
    environment.EnvironmentModelFacadeMixin
):
    pass


class Log(
    config.ConfigMixin,
    environment.EnvironmentModel
):
    user = django.ForeignKey(User, null=True, on_delete=django.PROTECT, related_name='+')
    command = django.CharField(max_length=256, null=True)
    messages = fields.EncryptedDataField(default=[])
    
    class Meta(environment.EnvironmentModel.Meta):
        facade_class = LogFacade

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = self.facade.hash(self.user, self.command, str(now()))
        
        super().save(*args, **kwargs)
