from systems.command.index import Command


class Stop(Command('db.stop')):

    def exec(self):
        self.log_result = False
        self.manager.stop_service(self, 'zimagi-postgres', self.remove)
        self.success('Successfully stopped PostgreSQL database service')
