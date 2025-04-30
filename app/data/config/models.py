from django.conf import settings
from systems.models.index import Model, ModelFacade
from utility.data import format_value


class ConfigFacade(ModelFacade("config")):
    def ensure(self, command, reinit, force):
        if settings.CLI_EXEC or settings.SCHEDULER_INIT:
            terminal_width = command.display_width

            if not reinit:
                command.notice("\n".join(["Loading Zimagi system configurations", "-" * terminal_width]))
                command.notice("-" * terminal_width)


class Config(Model("config")):
    def save(self, *args, **kwargs):
        self.value = format_value(self.value_type, self.value)
        super().save(*args, **kwargs)
