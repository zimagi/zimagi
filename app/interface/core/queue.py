from django.conf import settings

from settings.config import Config
from systems.command.types import queue


class StartCommand(
    queue.QueueActionCommand
):
    def server_enabled(self):
        return False

    def parse(self):
        self.parse_variable('memory', '--memory', str,
            'Redis queue memory size in g(GB)/m(MB)',
            value_label = 'NUM(g|m)',
            default = '250m'
        )

    def exec(self):
        self.manager.start_service(self, 'mcmi-queue',
            "redis:5", { 6379: None },
            docker_command = "redis-server --requirepass {}".format(
                Config.string('MCMI_REDIS_PASSWORD', 'mcmi')
            ),
            volumes = {
                'mcmi-queue': {
                    'bind': '/data',
                    'mode': 'rw'
                }
            },
            memory = self.options.get('memory'),
            wait = 20
        )
        self.success('Successfully started Redis queue service')


class StopCommand(
    queue.QueueActionCommand
):
    def server_enabled(self):
        return False

    def parse(self):
        self.parse_flag('remove', '--remove', 'remove container and service info after stopping')

    def exec(self):
        self.manager.stop_service(self, 'mcmi-queue', self.options.get('remove'))
        self.success('Successfully stopped Redis queue service')


class Command(queue.QueueRouterCommand):

    def get_subcommands(self):
        return (
            ('start', StartCommand),
            ('stop', StopCommand)
        )
