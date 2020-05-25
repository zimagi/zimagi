from systems.command.index import Command


class Action(Command('processor.stop')):

    def exec(self):
        def stop_service(name):
            self.manager.stop_service(self, name, self.remove)
            self.success("Successfully stopped {} service".format(name))

        self.run_list([
            'mcmi-scheduler',
            'mcmi-worker'
        ], stop_service)
