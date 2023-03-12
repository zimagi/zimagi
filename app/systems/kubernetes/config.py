from .base import KubeBase
from utility.data import normalize_value

import logging


logger = logging.getLogger(__name__)


class KubeConfig(KubeBase):

    def get(self, name, values = True):
        def get_info(cluster):
            config_map = cluster.core_api.read_namespaced_config_map(
                name,
                cluster.namespace,
                pretty = False
            )
            if not values:
                return config_map
            return normalize_value(config_map.data)

        return self.cluster.exec("get {} config".format(name), get_info, {})


    def update(self, name, **config):
        def update_config(cluster):
            config_map = self.get(name, False)
            if config_map.data is None:
                config_map.data = {}

            for key, value in config.items():
                config_map.data[key] = str(value)

            return cluster.core_api.patch_namespaced_config_map(
                name,
                cluster.namespace,
                config_map,
                pretty = False
            )
        return self.cluster.exec("update {} config".format(name), update_config)
