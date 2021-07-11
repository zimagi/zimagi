from systems.models.index import Model, ModelFacade


class HostFacade(ModelFacade('host')):

    def get_field_token_display(self, instance, value, short):
        if value and short:
            return super().get_field_token_display(instance, value[:10] + '...', short)
        return super().get_field_token_display(instance, value, short)


class Host(Model('host')):

    def save(self, *args, **kwargs):
        self.environment_id = Model('environment').facade.get_env()
        super().save(*args, **kwargs)
