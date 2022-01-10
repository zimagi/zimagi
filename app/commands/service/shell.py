from systems.commands.index import Command


class Shell(Command('service.shell')):

    def exec(self):
        self.manager.get_service_shell(self.service_name, shell = self.shell)
