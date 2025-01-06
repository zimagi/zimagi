import logging

from kubernetes import client

from .base import KubeBase

logger = logging.getLogger(__name__)


class KubeWorker(KubeBase):
    def get_spec(self, name):
        labels = self._get_labels(name, "worker")

        return client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=self._get_metadata_spec(labels, name),
            spec=client.V1JobSpec(
                ttl_seconds_after_finished=0,
                active_deadline_seconds=None,
                completion_mode="NonIndexed",
                completions=1,
                parallelism=1,
                template=self._get_pod_spec(
                    name, labels, ["zimagi-worker"], env={"ZIMAGI_WORKER_MAX_PROCESSES": "1"}, restart_policy="Never"
                ),
            ),
        )

    def create(self, name):
        def create_job(cluster):
            cluster.batch_api.create_namespaced_job(cluster.namespace, self.get_spec(name), pretty=False)

        return self.cluster.exec(f"create {self.type} job", create_job)

    def get_active_workers(self):
        def list_workers(cluster):
            return [
                job
                for job in cluster.batch_api.list_namespaced_job(
                    cluster.namespace, label_selector=f"worker-type={self.type}", limit=0, pretty=False
                ).items
                if job.status.active
            ]

        return self.cluster.exec(f"get active {self.type} workers", list_workers, [])
