import copy
import logging
import os

from django.conf import settings
from systems.kubernetes.cluster import KubeCluster
from utility.data import env_value, normalize_value
from utility.parallel import Parallel
from utility.text import interpolate
from utility.time import Time

logger = logging.getLogger(__name__)


class ManagerClusterMixin:
    def __init__(self):
        super().__init__()
        self.cluster = KubeCluster(self)

    def get_worker_spec(self, name):
        if not getattr(self, "_worker_spec", None):
            self._worker_spec = {}

        if name not in self._worker_spec:
            workers = self.get_spec("workers")

            environment = {"ZIMAGI_APP_NAME": self.app_name, "ZIMAGI_CLI_EXEC": False}
            worker = copy.deepcopy(workers[name])

            for env_name, value in dict(os.environ).items():
                if (env_name.startswith("KUBERNETES_") or env_name.startswith("ZIMAGI_")) and not env_name.endswith("_EXEC"):
                    environment[env_name] = value

            for setting in dir(settings):
                if setting == setting.upper():
                    value = getattr(settings, setting)
                    if isinstance(value, (int, float, bool, str)):
                        environment[setting] = env_value(value)

            self._worker_spec[name] = normalize_value(interpolate(worker, environment))
        return self._worker_spec[name]

    def get_global_config(self, values=True):
        return self.cluster.get_config(settings.KUBERNETES_GLOBAL_CONFIG, values)

    def update_global_config(self, **config):
        return self.cluster.update_config(settings.KUBERNETES_GLOBAL_CONFIG, **config)

    def get_scheduler_config(self, values=True):
        return self.cluster.get_config(settings.KUBERNETES_SCHEDULER_CONFIG, values)

    def update_scheduler_config(self, **config):
        return self.cluster.update_config(settings.KUBERNETES_SCHEDULER_CONFIG, **config)

    def get_worker_config(self, values=True):
        return self.cluster.get_config(settings.KUBERNETES_WORKER_CONFIG, values)

    def update_worker_config(self, **config):
        return self.cluster.update_config(settings.KUBERNETES_WORKER_CONFIG, **config)

    def get_command_config(self, values=True):
        return self.cluster.get_config(settings.KUBERNETES_COMMAND_CONFIG, values)

    def update_command_config(self, **config):
        return self.cluster.update_config(settings.KUBERNETES_COMMAND_CONFIG, **config)

    def get_data_config(self, values=True):
        return self.cluster.get_config(settings.KUBERNETES_DATA_CONFIG, values)

    def update_data_config(self, **config):
        return self.cluster.update_config(settings.KUBERNETES_DATA_CONFIG, **config)

    def restart_scheduler(self):
        self.update_scheduler_config(update_time=Time().now_string)

    def restart_services(self):
        update_time = Time().now_string

        def restart(name):
            self.cluster.update_config(name, update_time=update_time)

        Parallel.list(settings.KUBERNETES_SERVICE_CONFIGS, restart)
