from django.conf import settings
from kubernetes import client, config
from kubernetes.client.rest import ApiException

from .config import KubeConfig
from .worker import KubeWorker

import logging
import json


logger = logging.getLogger(__name__)


class ClusterError(Exception):
    pass


class KubeCluster(object):

    def __init__(self, manager):
        self.name = settings.KUBERNETES_BASE_NAME
        self.manager = manager

        self.cluster_connected = False
        self.cluster_config = KubeConfig(self)

        try:
            try:
                config.load_incluster_config()
            except Exception as e:
                config.load_kube_config()

            self.core_api = client.CoreV1Api()
            self.batch_api = client.BatchV1Api()
            self.cluster_connected = True

        except Exception as e:
            pass


    @property
    def namespace(self):
        if not settings.KUBERNETES_NAMESPACE:
            raise ClusterError("Environment variable KUBERNETES_NAMESPACE required when accessing Kubernetes service")
        return settings.KUBERNETES_NAMESPACE

    @property
    def pod_name(self):
        if not settings.KUBERNETES_POD_NAME:
            raise ClusterError("Environment variable KUBERNETES_POD_NAME required when accessing Kubernetes service")
        return settings.KUBERNETES_POD_NAME

    @property
    def pod(self):
        return self.get_pod(self.pod_name)


    def exec(self, name, callback, default = None):
        try:
            if self.cluster_connected:
                return callback(self)
            return default

        except ApiException as e:
            raise ClusterError("Kubernetes operation {} failed with [ {} ] - {}: {}".format(
              name,
              e.status,
              e.reason,
              json.dumps(json.loads(e.body), indent = 2)
            ))


    def get_pod(self, name):
        def get_info(cluster):
            return cluster.core_api.read_namespaced_pod(name, cluster.namespace, pretty = False)
        return self.exec("get pod {}".format(name), get_info)


    def get_config(self, name):
        return self.cluster_config.get(name)

    def update_config(self, name, **config):
        return self.cluster_config.update(name, **config)


    def create_worker(self, type, name):
        return KubeWorker(self, type).create(name)

    def get_active_workers(self, type):
        return KubeWorker(self, type).get_active_workers()
