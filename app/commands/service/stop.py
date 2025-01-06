from systems.commands.index import Command


class Stop(Command("service.stop")):
    def exec(self):
        self.disable_logging()

        def stop_service(service_name):
            self.manager.stop_service(service_name)
            self.success(f"Successfully stopped service: {service_name}")

        self.run_list(self.manager.expand_service_names(self.service_names), stop_service)
