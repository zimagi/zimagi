from systems.command.index import Command


class Action(Command('db.stop')):

    def exec(self):
        self.log_result = False
        self.manager.stop_service(self, 'mcmi-postgres', self.remove)
        self.success('Successfully stopped PostgreSQL database service')
