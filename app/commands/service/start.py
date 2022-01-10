from systems.commands.index import Command


class Start(Command('service.start')):

    def exec(self):
        service_names = self.service_names if self.service_names else self.manager.service_names

        def restart_service(service_name):
            self.manager.get_service(service_name, wait = self.wait)
            self.success("Successfully started service: {}".format(service_name))

        self.run_list(service_names, restart_service)
