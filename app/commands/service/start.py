from systems.commands.index import Command


class Start(Command("service.start")):
    def exec(self):
        service_names = self.manager.expand_service_names(self.service_names)
        self.manager.initialize_services(service_names)
        self.success("Successfully started services: {}".format(", ".join(service_names)))
