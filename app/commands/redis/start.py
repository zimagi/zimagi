from settings.config import Config
from systems.commands.index import Command


class Start(Command('redis.start')):

    def exec(self):
        self.manager.start_service(self, 'zimagi-redis',
            "redis:5", { 6379: None },
            docker_command = "redis-server --requirepass {}".format(
                Config.string('ZIMAGI_REDIS_PASSWORD', 'zimagi')
            ),
            volumes = {
                'zimagi-redis': {
                    'bind': '/data',
                    'mode': 'rw'
                }
            },
            memory = self.memory,
            wait = 20
        )
        self.set_state('config_ensure', True)
        self.success('Successfully started Redis service')
