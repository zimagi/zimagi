from django.conf import settings
from kubernetes import client, config
from kubernetes.client.rest import ApiException

from utility.data import normalize_value
from utility.parallel import Parallel
from utility.time import Time

import logging


logger = logging.getLogger(__name__)


class ClusterError(Exception):
    pass


class ManagerClusterMixin(object):

    def __init__(self):
        super().__init__()

        self.kube_core_api = None
        self.cluster_connected = False
        try:
            try:
                config.load_incluster_config()
            except Exception as e:
                config.load_kube_config()

            self.kube_core_api = client.CoreV1Api()
            self.cluster_connected = True

        except Exception as e:
            pass


    @property
    def cluster_namespace(self):
        if not settings.KUBERNETES_NAMESPACE:
            raise ClusterError("Environment variable KUBERNETES_NAMESPACE required when accessing Kubernetes service")
        return settings.KUBERNETES_NAMESPACE


    def get_pod_name(self):
        if not settings.KUBERNETES_POD_NAME:
            raise ClusterError("Environment variable KUBERNETES_POD_NAME required when accessing Kubernetes service")
        return settings.KUBERNETES_POD_NAME

    def get_service_pod(self, name):
        def get_info():
            return self.kube_core_api.read_namespaced_pod(name, self.cluster_namespace, pretty = False)
        return self._kube_exec("get service pod {}".format(name), get_info)


    def get_global_config(self, values = True):
        return self._get_config(settings.KUBERNETES_GLOBAL_CONFIG, values)

    def update_global_config(self, **config):
        return self._update_config(settings.KUBERNETES_GLOBAL_CONFIG, **config)


    def get_scheduler_config(self, values = True):
        return self._get_config(settings.KUBERNETES_SCHEDULER_CONFIG, values)

    def update_scheduler_config(self, **config):
        return self._update_config(settings.KUBERNETES_SCHEDULER_CONFIG, **config)


    def get_worker_config(self, values = True):
        return self._get_config(settings.KUBERNETES_WORKER_CONFIG, values)

    def update_worker_config(self, **config):
        return self._update_config(settings.KUBERNETES_WORKER_CONFIG, **config)


    def get_command_config(self, values = True):
        return self._get_config(settings.KUBERNETES_COMMAND_CONFIG, values)

    def update_command_config(self, **config):
        return self._update_config(settings.KUBERNETES_COMMAND_CONFIG, **config)


    def get_data_config(self, values = True):
        return self._get_config(settings.KUBERNETES_DATA_CONFIG, values)

    def update_data_config(self, **config):
        return self._update_config(settings.KUBERNETES_DATA_CONFIG, **config)


    def restart_scheduler(self):
        self.update_scheduler_config(update_time = Time().now_string)

    def restart_services(self):
        update_time = Time().now_string

        def restart(name):
            self._update_config(name, update_time = update_time)

        Parallel.list(settings.KUBERNETES_SERVICE_CONFIGS, restart)


    def _kube_exec(self, name, callback, default = None):
        try:
            if self.cluster_connected:
                return callback()
            return default

        except ApiException as e:
            raise ClusterError("Kubernetes operation {} failed with: {}", name, e)


    def _get_config(self, name, values = True):
        def get_info():
            config_map = self.kube_core_api.read_namespaced_config_map(
                name,
                self.cluster_namespace,
                pretty = False
            )
            if not values:
                return config_map
            return normalize_value(config_map.data)

        return self._kube_exec("get {} config".format(name), get_info, {})

    def _update_config(self, name, **config):
        def update():
            config_map = self._get_config(name, False)
            if config_map.data is None:
                config_map.data = {}

            for key, value in config.items():
                config_map.data[key] = str(value)

            return self.kube_core_api.patch_namespaced_config_map(
                name,
                self.cluster_namespace,
                config_map,
                pretty = False
            )
        return self._kube_exec("update {} config".format(name), update)
