from django.conf import settings

from systems.plugins.index import BaseProvider
from utility.data import dump_json

import re


class Provider(BaseProvider('worker', 'docker')):

    @property
    def agent_name(self):
        if not getattr(self, '_agent_name', None):
            self._agent_name = "-".join(re.split(r'\s+', self.field_command_name))
        return self._agent_name

    @property
    def worker_name(self):
        if not getattr(self, '_worker_name', None):
            self._worker_name = "worker-{}".format(self.field_worker_type)
        return self._worker_name


    def check_agent(self):
        return True if self.manager.get_service(self.agent_name, create = False) else False

    def start_agent(self):
        self.command.notice("Starting agent {} at {}".format(self.agent_name, self.command.time.now_string))
        self.manager.stop_service(self.agent_name, remove = True)
        self.manager.start_service(self.agent_name,
            template = 'agent',
            command = "{} --json='{}'".format(self.field_command_name, dump_json(self.field_command_options)),
            **self._get_service_spec('agent')
        )

    def stop_agent(self):
        self.command.notice("Stopping agent {} at {}".format(self.agent_name, self.command.time.now_string))
        self.manager.stop_service(self.agent_name, remove = True)


    def check_workers(self):
        return 0 if self.manager.get_service(self.worker_name, create = False) else 1

    def start_worker(self, name):
        self.command.notice("Starting worker {} at {}".format(self.worker_name, self.command.time.now_string))
        self.manager.stop_service(self.worker_name, remove = True)
        self.manager.start_service(self.worker_name,
            template = 'worker',
            **self._get_service_spec('worker')
        )


    def _get_service_spec(self, service_type):
        worker_spec = self.manager.get_worker_spec(self.field_worker_type)
        service_spec = self.manager.get_service_spec(service_type)

        if worker_spec.get('docker_runtime', None):
            service_spec['runtime'] = worker_spec['docker_runtime']

        service_spec['image'] = worker_spec.get('image', settings.RUNTIME_IMAGE)

        service_spec['environment']['ZIMAGI_WORKER_TYPE'] = self.field_worker_type
        for name, value in worker_spec.get('env', {}).items():
            service_spec['environment'][name] = str(value)

        return service_spec
