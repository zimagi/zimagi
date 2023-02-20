from systems.plugins.index import BaseProvider


class Provider(BaseProvider('worker', 'docker')):

    def check_worker(self):
        return self.manager.get_service('worker',
            restart = False,
            create = False
        )

    def start_worker(self):
        self.manager.stop_service('worker', remove = True)

        service_spec = self.manager.get_service_spec('worker')
        service_spec['environment']['ZIMAGI_WORKER_TYPE'] = self.field_worker_type

        self.manager.start_service('worker', **service_spec)
