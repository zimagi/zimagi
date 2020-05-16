from django.conf import settings
from django.db import models as django

from data.environment import models as environment
from systems.models import fields


class HostFacade(
    environment.EnvironmentBaseFacadeMixin
):
    def get_packages(self):
        return ['host']

    def get_field_token_display(self, instance, value, short):
        if value and short:
            return self.encrypted_color(value[:10] + '...')
        else:
            return self.encrypted_color(str(value))


class Host(
    environment.EnvironmentBase
):
    host = django.URLField()
    port = django.IntegerField(default = 5123)
    user = django.CharField(max_length = 150, default = settings.ADMIN_USER)
    token = fields.EncryptedCharField(max_length = 256, default = settings.DEFAULT_ADMIN_TOKEN)

    class Meta(environment.EnvironmentBase.Meta):
        verbose_name = "host"
        verbose_name_plural = "hosts"
        facade_class = HostFacade

    def __str__(self):
        return "{}".format(self.name)
