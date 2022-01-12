from systems.commands.index import Command


class Destroy(Command('service.destroy')):

    def exec(self):
        self.log_result = False
        service_names = self.service_names if self.service_names else self.manager.service_names

        def destroy_service(service_name):
            self.manager.stop_service(service_name,
                remove = True,
                remove_volumes = self.remove_volumes,
                remove_image = self.remove_image,
                remove_network = not self.keep_network
            )
            self.success("Successfully destroyed service: {}".format(service_name))

        self.run_list(service_names, destroy_service)
