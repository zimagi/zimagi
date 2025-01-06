import logging

from utility.data import normalize_value

logger = logging.getLogger(__name__)


class KubeConfig:
    def __init__(self, cluster):
        self.cluster = cluster

    def get(self, name, values=True):
        def get_info(cluster):
            config_map = cluster.core_api.read_namespaced_config_map(name, cluster.namespace, pretty=False)
            if not values:
                return config_map
            return normalize_value(config_map.data)

        return self.cluster.exec(f"get {name} config", get_info, {})

    def update(self, name, **config):
        def update_config(cluster):
            config_map = self.get(name, False)
            if config_map.data is None:
                config_map.data = {}

            for key, value in config.items():
                config_map.data[key] = str(value)

            return cluster.core_api.patch_namespaced_config_map(name, cluster.namespace, config_map, pretty=False)

        return self.cluster.exec(f"update {name} config", update_config)
