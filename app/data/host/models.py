from systems.models.index import ModelFacade


class HostFacade(ModelFacade('host')):

    def get_field_token_display(self, instance, value, short):
        if value and short:
            return super().get_field_token_display(instance, value[:10] + '...', short)
        return super().get_field_token_display(instance, value, short)

    def get_field_encryption_key_display(self, instance, value, short):
        if value and short:
            return super().get_field_encryption_key_display(instance, value[:10] + '...', short)
        return super().get_field_encryption_key_display(instance, value, short)
