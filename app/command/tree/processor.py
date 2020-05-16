from django.conf import settings

from settings.roles import Roles
from base.command.router import RouterCommand
from base.command.action import ActionCommand

import os


class ProcessorRouterCommand(RouterCommand):

    def get_priority(self):
        return 95


class ProcessorActionCommand(
    ActionCommand
):

    def groups_allowed(self):
        return [
            Roles.admin,
            Roles.processor_admin
        ]

    def server_enabled(self):
        return True

    def get_priority(self):
        return 95


class StartCommand(
    ProcessorActionCommand
):
    def server_enabled(self):
        return False

    def parse(self):
        self.parse_variable('scheduler_memory', '--sched-memory', str,
            'scheduler memory size in g(GB)/m(MB)',
            value_label = 'NUM(g|m)',
            default = '250m'
        )
        self.parse_variable('worker_memory', '--work-memory', str,
            'worker memory size in g(GB)/m(MB)',
            value_label = 'NUM(g|m)',
            default = '250m'
        )


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
            ('mcmi-scheduler', self.options.get('scheduler_memory')),
            ('mcmi-worker', self.options.get('worker_memory'))
        ], start_service)


class StopCommand(
    ProcessorActionCommand
):
    def server_enabled(self):
        return False

    def parse(self):
        self.parse_flag('remove', '--remove', 'remove container and service info after stopping')

    def exec(self):
        def stop_service(name):
            self.manager.stop_service(self, name, self.options.get('remove'))
            self.success("Successfully stopped {} service".format(name))

        self.run_list([
            'mcmi-scheduler',
            'mcmi-worker'
        ], stop_service)


class Command(ProcessorRouterCommand):

    def get_subcommands(self):
        return (
            ('start', StartCommand),
            ('stop', StopCommand)
        )
