from functools import lru_cache

from django.conf import settings
from settings import core as app_settings
from systems.models.index import Model, ModelFacade
from utility.data import format_value
from utility.environment import Environment


class ConfigFacade(ModelFacade("config")):
    def ensure(self, command, reinit, force):
        if settings.CLI_EXEC or settings.SCHEDULER_INIT:
            terminal_width = command.display_width

            if not reinit:
                command.notice("\n".join(["Loading Zimagi system configurations", "-" * terminal_width]))

            command.config_provider.store(
                "environment", {"value": Environment.get_active_env(), "value_type": "str", "groups": ["system"]}
            )
            if not reinit:
                command.notice("-" * terminal_width)

    def keep(self, key=None):
        if key:
            return []

        keep = ["environment"]
        for setting in self.get_settings():
            keep.append(setting["name"])
        return keep

    @lru_cache(maxsize=None)
    def get_settings(self):
        settings_variables = []
        for setting in dir(app_settings):
            if setting == setting.upper():
                value = getattr(app_settings, setting)
                value_type = type(value).__name__

                if value_type in ("bool", "int", "float", "str", "list", "dict"):
                    settings_variables.append(
                        {"name": f"{settings.APP_SERVICE.upper()}_{setting}", "value": value, "type": value_type}
                    )
        return settings_variables


class Config(Model("config")):
    def save(self, *args, **kwargs):
        self.value = format_value(self.value_type, self.value)
        super().save(*args, **kwargs)
