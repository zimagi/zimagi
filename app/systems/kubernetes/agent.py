import logging

from kubernetes import client
from utility.data import ensure_list

from .base import KubeBase

logger = logging.getLogger(__name__)


class KubeAgent(KubeBase):
    def get_spec(self, name, command, count=1):
        type = "agent"
        labels = self._get_labels(name, type)

        if not command:
            command = []

        return client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=self._get_metadata_spec(labels, name),
            spec=client.V1DeploymentSpec(
                replicas=count,
                revision_history_limit=2,
                selector=client.V1LabelSelector(match_labels=self._get_selector_labels(name, type)),
                template=self._get_pod_spec(
                    name,
                    labels,
                    ["zimagi", *ensure_list(command)],
                    env={"ZIMAGI_CLI_EXEC": "True", "ZIMAGI_WORKER_EXEC": "True"},
                    restart_policy="Always",
                ),
            ),
        )

    def check(self, name):
        try:
            self.cluster.apps_api.read_namespaced_deployment(name, self.cluster.namespace)

        except client.ApiException as e:
            if e.status == 404:
                return False
            else:
                raise e
        return True

    def get(self, name):
        try:
            deployment = self.cluster.apps_api.read_namespaced_deployment(name, self.cluster.namespace)

        except client.ApiException as e:
            if e.status == 404:
                return None
            else:
                raise e
        return deployment

    def scale(self, name, command, count=1):
        def scale_agent(cluster):
            if count == 0:
                deployment = self.get(name)
                if deployment:
                    cluster.apps_api.delete_namespaced_deployment(name, namespace=cluster.namespace)
            else:
                deployment = self.get(name)
                if not deployment:
                    cluster.apps_api.create_namespaced_deployment(
                        namespace=cluster.namespace, body=self.get_spec(name, command, count), pretty=False
                    )
                elif deployment.spec.replicas != count:
                    deployment.spec.replicas = count
                    cluster.apps_api.patch_namespaced_deployment(
                        name=name, namespace=cluster.namespace, body=deployment, pretty=False
                    )

        return self.cluster.exec(f"scale {self.type} agent", scale_agent)
