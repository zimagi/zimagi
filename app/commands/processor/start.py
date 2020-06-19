from django.conf import settings

from systems.commands.index import Command

import os


class Start(Command('processor.start')):

    def get_service_config(self):
        config = {
            'ZIMAGI_LOG_LEVEL': settings.LOG_LEVEL,
            'ZIMAGI_WORKER_CONCURRENCY': 2
        }
        for name, value in dict(os.environ).items():
            if name.startswith('ZIMAGI_') and name != 'ZIMAGI_CLI_EXEC':
                config[name] = value

        return config


    def start_dependencies(self):
        def start_dependency(name):
            self.exec_local("{} start".format(name))

        self.run_list(['queue'], start_dependency)


    def exec(self):
        self.start_dependencies()

        def start_service(info):
            self.manager.start_service(self, info[0],
                self.environment_image, {},
                docker_entrypoint = info[0],
                network_mode = 'host',
                environment = self.get_service_config(),
                volumes = {
                    '/var/run/docker.sock': {
                        'bind': '/var/run/docker.sock',
                        'mode': 'rw'
                    },
                    '/usr/local/share/zimagi': {
                        'bind': '/usr/local/share/zimagi',
                        'mode': 'ro'
                    },
                    '/usr/local/lib/zimagi': {
                        'bind': '/usr/local/lib/zimagi',
                        'mode': 'rw'
                    },
                    '/var/local/zimagi': {
                        'bind': '/var/local/zimagi',
                        'mode': 'rw'
                    }
                },
                memory = info[1],
                wait = 20
            )
            self.success("Successfully started {} service".format(info[0]))

        self.run_list([
            ('zimagi-scheduler', self.scheduler_memory),
            ('zimagi-worker', self.worker_memory)
        ], start_service)
