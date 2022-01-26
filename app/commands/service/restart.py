from systems.commands.index import Command


class Restart(Command('service.restart')):

    def exec(self):
        self.disable_logging()
        
        service_names = self.service_names if self.service_names else self.manager.service_names

        def restart_service(service_name):
            self.manager.stop_service(service_name)
            self.manager.get_service(service_name)
            self.success("Successfully restarted service: {}".format(service_name))

        self.run_list(service_names, restart_service)
