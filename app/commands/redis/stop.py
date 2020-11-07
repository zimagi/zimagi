from systems.commands.index import Command


class Stop(Command('redis.stop')):

    def exec(self):
        self.manager.stop_service(self, 'zimagi-redis', self.remove)
        self.set_state('config_ensure', True)
        self.success('Successfully stopped Redis service')
