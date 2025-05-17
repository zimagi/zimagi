from django.conf import settings
from systems.manage.service import ServiceError
from systems.plugins.index import BaseProvider
from utility.data import dump_json


class Provider(BaseProvider("worker", "docker")):

    def check_agent(self, agent_name):
        return self.manager.get_service(agent_name, create=False)

    def start_agent(self, agent_name):
        self.manager.stop_service(agent_name, remove=True)
        self.manager.start_service(
            agent_name,
            template="agent",
            command=f"{self.field_command_name} --json='{dump_json(self.field_command_options)}'",
            **self._get_service_spec("agent"),
        )

    def stop_agent(self, agent_name):
        self.manager.stop_service(agent_name, remove=True)

    def get_worker_count(self):
        return len(self.manager.get_worker_services(self.field_worker_type))

    def start_worker(self, name):
        name = name.replace("_", "-")
        self.manager.stop_service(name, remove=True)
        self.manager.start_service(name, template="worker", **self._get_service_spec("worker"))

    def _get_service_spec(self, service_type):
        worker_spec = self.manager.get_worker_spec(self.field_worker_type)
        spec_name = f"{service_type}.{settings.APP_ENVIRONMENT}"
        service_spec = self.manager.get_service_spec(spec_name)

        if not service_spec:
            spec_name = spec_name.split(".")[0]
            service_spec = self.manager.get_service_spec(spec_name)

        if not service_spec:
            raise ServiceError(f"Service specification for '{spec_name}' does not exist")

        if worker_spec.get("docker_runtime", None):
            service_spec["runtime"] = worker_spec["docker_runtime"]

        service_spec["image"] = worker_spec.get("image", settings.RUNTIME_IMAGE)

        service_spec["environment"]["ZIMAGI_WORKER_TYPE"] = self.field_worker_type
        for name, value in worker_spec.get("env", {}).items():
            service_spec["environment"][name] = str(value)

        return service_spec
