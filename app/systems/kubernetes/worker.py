from django.conf import settings
from kubernetes import client, config

from settings.config import Config
from .base import KubeBase

import logging


logger = logging.getLogger(__name__)


class KubeWorker(KubeBase):

    def __init__(self, cluster, type):
        super().__init__(cluster)

        self.type = type
        self.spec = cluster.manager.get_worker_spec(type)


    def get_spec(self, name):
        labels = {
            'worker-type': self.type,
            'worker-name': name
        }

        image_pull_secrets = []
        for secret_name in settings.KUBERNETES_IMAGE_PULL_SECRETS:
            image_pull_secrets.append(client.V1LocalObjectReference(name = secret_name))

        worker_env = self.spec.get('env', {})
        env = [
            client.V1EnvVar(
                name = 'ZIMAGI_WORKER_TYPE',
                value = self.type
            ),
            client.V1EnvVar(
                name = 'ZIMAGI_WORKER_MAX_PROCESSES',
                value = '1'
            )
        ]
        for env_name in [
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

        volumes = []
        volume_mounts = []

        # Production / Testing
        if settings.KUBERNETES_LIB_PVC:
            image_pull_policy = 'IfNotPresent'
            node_selector = {
                'service': "worker-{}".format(self.type)
            }
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

        # Development
        elif settings.HOST_APP_DIR and settings.HOST_LIB_DIR:
            image_pull_policy = 'Never'
            node_selector = {}
            volumes = [
                client.V1Volume(
                    name = 'app-source',
                    host_path = client.V1HostPathVolumeSource(
                        path = settings.HOST_APP_DIR,
                        type = "Directory",
                    )
                ),
                client.V1Volume(
                    name = 'app-lib',
                    host_path = client.V1HostPathVolumeSource(
                        path = settings.HOST_LIB_DIR,
                        type = "Directory",
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

        return client.V1Job(
            api_version = 'batch/v1',
            kind = 'Job',
            metadata = client.V1ObjectMeta(
                namespace = self.cluster.namespace,
                name = name,
                labels = labels,
                annotations = {}
            ),
            spec = client.V1JobSpec(
                ttl_seconds_after_finished = 0,
                active_deadline_seconds = None,
                completion_mode = 'NonIndexed',
                completions = 1,
                parallelism = 1,
                template = client.V1PodTemplateSpec(
                    metadata = client.V1ObjectMeta(
                        labels = labels
                    ),
                    spec = client.V1PodSpec(
                        hostname = name,
                        restart_policy = 'Never',
                        service_account_name = settings.KUBERNETES_WORKER_SERVICE_ACCOUNT,
                        automount_service_account_token = True,
                        enable_service_links = True,
                        active_deadline_seconds = None,
                        image_pull_secrets = image_pull_secrets,
                        node_selector = node_selector,
                        containers = [
                            client.V1Container(
                                name = name,
                                image = self.spec.get('image', settings.RUNTIME_IMAGE),
                                image_pull_policy = image_pull_policy,
                                command = ['zimagi-worker'],
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
                        ],
                        volumes = volumes
                    )
                )
            )
        )

    def create(self, name):
        def create_job(cluster):
            cluster.batch_api.create_namespaced_job(cluster.namespace, self.get_spec(name),
                pretty = False
            )
        return self.cluster.exec("create {} job".format(self.type), create_job)


    def get_active_workers(self):
        def list_workers(cluster):
            return [ job for job in cluster.batch_api.list_namespaced_job(
                cluster.namespace,
                label_selector = "worker-type={}".format(self.type),
                limit = 0,
                pretty = False
            ).items if job.status.active ]

        return self.cluster.exec("get active {} workers".format(self.type), list_workers, [])
