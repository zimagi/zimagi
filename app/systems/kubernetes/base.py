from django.conf import settings
from kubernetes import client, config

from settings.config import Config


class KubeBase(object):

    def __init__(self, cluster, type):
        self.type = type
        self.cluster = cluster
        self.spec = cluster.manager.get_worker_spec(type)


    def _check_development(self):
        # Production / Testing
        if settings.KUBERNETES_LIB_PVC:
            return False
        # Development
        return True


    def _get_labels(self, name, type):
        pod = self.cluster.pod
        pod_labels = pod.metadata.labels

        return {
            'app.kubernetes.io/name': name,
            'app.kubernetes.io/component': "{}-{}".format(type, self.type),
            'app.kubernetes.io/managed-by': 'Zimagi',
            'app.kubernetes.io/instance': pod_labels['app.kubernetes.io/instance'],
            'worker-type': self.type,
            'worker-name': name
        }

    def _get_selector_labels(self, name, type):
        pod = self.cluster.pod
        pod_labels = pod.metadata.labels

        return {
            'app.kubernetes.io/name': name,
            'app.kubernetes.io/component': "{}-{}".format(type, self.type),
            'app.kubernetes.io/instance': pod_labels['app.kubernetes.io/instance']
        }


    def _get_pull_secrets(self):
        image_pull_secrets = []

        for secret_name in settings.KUBERNETES_IMAGE_PULL_SECRETS:
            image_pull_secrets.append(client.V1LocalObjectReference(name = secret_name))

        return image_pull_secrets


    def _get_pull_policy(self):
        image_pull_policy = 'Never'

        if not self._check_development():
            image_pull_policy = 'IfNotPresent'

        return image_pull_policy

    def _get_node_selector(self):
        node_selector = {}

        if not self._check_development():
            node_selector = {
                'service': "worker-{}".format(self.type)
            }
        return node_selector



    def _get_env(self, env_params = None):
        if not env_params:
            env_params = {}

        worker_env = self.spec.get('env', {})
        env = [
            client.V1EnvVar(
                name = 'KUBERNETES_NAMESPACE',
                value_from = client.V1EnvVarSource(
                    field_ref = client.V1ObjectFieldSelector(
                        field_path = 'metadata.namespace'
                    )
                )
            ),
            client.V1EnvVar(
                name = 'KUBERNETES_POD_NAME',
                value_from = client.V1EnvVarSource(
                    field_ref = client.V1ObjectFieldSelector(
                        field_path = 'metadata.name'
                    )
                )
            ),
            client.V1EnvVar(
                name = 'ZIMAGI_WORKER_PROVIDER',
                value = 'kubernetes'
            ),
            client.V1EnvVar(
                name = 'ZIMAGI_WORKER_TYPE',
                value = self.type
            )
        ]
        for env_name, env_value in env_params.items():
            env.append(client.V1EnvVar(
                name = env_name,
                value = str(env_value)
            ))

        for env_name in [
            'KUBERNETES_WORKER_SERVICE_ACCOUNT',
            'ZIMAGI_GLOBAL_CONFIG_MAP',
            'ZIMAGI_WORKER_CONFIG_MAP',
            'ZIMAGI_GLOBAL_SECRET',
            'ZIMAGI_DEFAULT_RUNTIME_IMAGE',
            'ZIMAGI_POSTGRES_HOST',
            'ZIMAGI_POSTGRES_PORT',
            'ZIMAGI_POSTGRES_USER',
            'ZIMAGI_POSTGRES_DB',
            'ZIMAGI_REDIS_HOST',
            'ZIMAGI_REDIS_PORT'
        ]:
            env_value = Config.value(env_name, None)
            if env_name not in worker_env and env_value is not None:
                env.append(client.V1EnvVar(
                    name = env_name,
                    value = str(env_value)
                ))
        for env_name, env_value in self.spec.get('env', {}).items():
            env.append(client.V1EnvVar(
                name = env_name,
                value = str(env_value)
            ))

        return env


    def _get_volume_mounts(self):
        volumes = []
        volume_mounts = []

        if not self._check_development():
            volumes = [
                client.V1Volume(
                    name = settings.KUBERNETES_LIB_PVC,
                    persistent_volume_claim = client.V1PersistentVolumeClaimVolumeSource(
                        claim_name = settings.KUBERNETES_LIB_PVC,
                        read_only = False
                    )
                )
            ]
            volume_mounts = [
                client.V1VolumeMount(
                    name = settings.KUBERNETES_LIB_PVC,
                    mount_path = settings.ROOT_LIB_DIR,
                    read_only = False
                )
            ]
        else:
            volumes = [
                client.V1Volume(
                    name = 'app-source',
                    host_path = client.V1HostPathVolumeSource(
                        path = settings.HOST_APP_DIR,
                        type = 'Directory',
                    )
                ),
                client.V1Volume(
                    name = 'app-lib',
                    host_path = client.V1HostPathVolumeSource(
                        path = settings.HOST_LIB_DIR,
                        type = 'Directory',
                    )
                )
            ]
            volume_mounts = [
                client.V1VolumeMount(
                    name = 'app-source',
                    mount_path = settings.APP_DIR,
                    read_only = False
                ),
                client.V1VolumeMount(
                    name = 'app-lib',
                    mount_path = settings.ROOT_LIB_DIR,
                    read_only = False
                )
            ]
        return volumes, volume_mounts


    def _get_metadata_spec(self, labels, name = None):
        if name:
            metadata = client.V1ObjectMeta(
                namespace = self.cluster.namespace,
                name = name,
                labels = labels,
                annotations = {}
            )
        else:
            metadata = client.V1ObjectMeta(
                labels = labels
            )
        return metadata


    def _get_container_spec(self, name, command, env, volume_mounts):
        return client.V1Container(
            name = name,
            image = self.spec.get('image', settings.RUNTIME_IMAGE),
            image_pull_policy = self._get_pull_policy(),
            command = command,
            env = env,
            env_from = [
                client.V1EnvFromSource(
                    config_map_ref = client.V1ConfigMapEnvSource(
                        name = settings.KUBERNETES_GLOBAL_CONFIG,
                        optional = False
                    )
                ),
                client.V1EnvFromSource(
                    config_map_ref = client.V1ConfigMapEnvSource(
                        name = settings.KUBERNETES_WORKER_CONFIG,
                        optional = False
                    )
                ),
                client.V1EnvFromSource(
                    secret_ref = client.V1SecretEnvSource(
                        name = settings.KUBERNETES_GLOBAL_SECRET,
                        optional = False
                    )
                )
            ],
            resources = client.V1ResourceRequirements(
                requests = {
                    'cpu': self.spec.get('kube_cpu_min', '750m'),
                    'memory': self.spec.get('kube_memory_min', '250Mi')
                },
                limits = {
                    'cpu': self.spec.get('kube_cpu_max', '1000m'),
                    'memory': self.spec.get('kube_memory_max', '500Mi')
                }
            ),
            volume_mounts = volume_mounts
        )


    def _get_pod_spec(self, name, labels, command, env = None, restart_policy = 'Never'):
        env = self._get_env(env)
        volumes, mounts = self._get_volume_mounts()

        return client.V1PodTemplateSpec(
            metadata = self._get_metadata_spec(labels),
            spec = client.V1PodSpec(
                hostname = name,
                restart_policy = restart_policy,
                service_account_name = settings.KUBERNETES_WORKER_SERVICE_ACCOUNT,
                automount_service_account_token = True,
                enable_service_links = True,
                active_deadline_seconds = None,
                image_pull_secrets = self._get_pull_secrets(),
                node_selector = self._get_node_selector(),
                containers = [
                    self._get_container_spec(name, command, env, mounts)
                ],
                volumes = volumes
            )
        )
