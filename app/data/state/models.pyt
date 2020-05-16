from django.db import models as django

from data.environment import models as environment
from systems.models import fields


class StateFacade(
    environment.EnvironmentBaseFacadeMixin
):
    def get_field_value_display(self, instance, value, short):
        if value is not None and isinstance(value, (list, tuple, dict)):
            return self.encrypted_color(yaml.dump(value))
        else:
            return self.encrypted_color(str(value))


class State(
    environment.EnvironmentBase
):
    value = fields.EncryptedDataField(null = True)

    class Meta(environment.EnvironmentBase.Meta):
        verbose_name = "state"
        verbose_name_plural = "states"
        facade_class = StateFacade
