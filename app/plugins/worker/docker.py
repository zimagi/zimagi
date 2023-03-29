from django.conf import settings

from systems.plugins.index import BaseProvider


class Provider(BaseProvider('worker', 'docker')):

    @property
    def worker_name(self):
        return "worker-{}".format(self.field_worker_type)


    def check_workers(self):
        return 0 if self.manager.get_service(self.worker_name, create = False) else 1

    def start_worker(self, name):
        worker_spec = self.manager.get_worker_spec(self.field_worker_type)
        service_spec = self.manager.get_service_spec('worker')

        if worker_spec.get('docker_runtime', None):
            service_spec['runtime'] = worker_spec['docker_runtime']

        service_spec['image'] = worker_spec.get('image', settings.RUNTIME_IMAGE)
        service_spec['environment']['ZIMAGI_WORKER_TYPE'] = self.field_worker_type
        for env_name, env_value in worker_spec.get('env', {}).items():
            service_spec['environment'][env_name] = str(env_value)

        self.manager.stop_service(self.worker_name, remove = True)
        self.manager.start_service(self.worker_name, template = 'worker', **service_spec)
