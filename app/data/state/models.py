from django.db import models as django

from systems.models import fields, environment


class StateFacade(
    environment.EnvironmentModelFacadeMixin
):
    def get_field_value_display(self, instance, value, short):
        if value is not None and instance.value_type in ('list', 'dict'):
            return self.encrypted_color(yaml.dump(value))
        else:
            return self.encrypted_color(str(value))



class State(
    environment.EnvironmentModel
):
    value = fields.EncryptedDataField(null = True)

    class Meta(environment.EnvironmentModel.Meta):
        verbose_name = "state"
        verbose_name_plural = "states"
        facade_class = StateFacade
