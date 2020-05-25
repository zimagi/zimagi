from django.conf import settings

from systems.command.index import Command

import os


class Action(Command('processor.start')):

    def get_service_config(self):
        config = {
            'MCMI_LOG_LEVEL': settings.LOG_LEVEL,
            'MCMI_WORKER_CONCURRENCY': 2
        }
        for name, value in dict(os.environ).items():
            if name.startswith('MCMI_') and name != 'MCMI_CLI_EXEC':
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
                    '/usr/local/share/mcmi': {
                        'bind': '/usr/local/share/mcmi',
                        'mode': 'ro'
                    },
                    '/usr/local/lib/mcmi': {
                        'bind': '/usr/local/lib/mcmi',
                        'mode': 'rw'
                    },
                    '/var/local/mcmi': {
                        'bind': '/var/local/mcmi',
                        'mode': 'rw'
                    }
                },
                memory = info[1],
                wait = 20
            )
            self.success("Successfully started {} service".format(info[0]))

        self.run_list([
            ('mcmi-scheduler', self.scheduler_memory),
            ('mcmi-worker', self.worker_memory)
        ], start_service)
