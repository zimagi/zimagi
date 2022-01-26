from systems.commands.index import Command


class Stop(Command('service.stop')):

    def exec(self):
        self.disable_logging()

        service_names = self.service_names if self.service_names else self.manager.service_names

        def stop_service(service_name):
            self.manager.stop_service(service_name)
            self.success("Successfully stopped service: {}".format(service_name))

        self.run_list(service_names, stop_service)
