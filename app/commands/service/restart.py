from systems.commands.index import Command


class Restart(Command('service.restart')):

    def exec(self):
        self.disable_logging()

        def restart_service(service_name):
            self.manager.stop_service(service_name)
            self.manager.get_service(service_name)
            self.success("Successfully restarted service: {}".format(service_name))

        self.run_list(
            self.manager.expand_service_names(self.service_names),
            restart_service
        )
