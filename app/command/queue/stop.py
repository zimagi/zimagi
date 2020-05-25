from systems.command.index import Command


class Action(Command('queue.stop')):

    def exec(self):
        self.manager.stop_service(self, 'mcmi-queue', self.remove)
        self.set_state('config_ensure', True)
        self.success('Successfully stopped Redis queue service')
