from django.utils.timezone import now
from systems.models.index import Model, ModelFacade
from utility.data import create_token


class ScalingEventFacade(ModelFacade("scaling_event")):
    pass


class ScalingEvent(Model("scaling_event")):

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = f"{now().strftime("%Y%m%d%H%M%S")}{create_token(5)}x"
        super().save(*args, **kwargs)
