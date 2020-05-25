from settings.config import Config
from systems.command.index import Command


class Action(Command('queue.start')):

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
            memory = self.memory,
            wait = 20
        )
        self.set_state('config_ensure', True)
        self.success('Successfully started Redis queue service')
