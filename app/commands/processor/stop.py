from systems.commands.index import Command


class Stop(Command('processor.stop')):

    def exec(self):
        def stop_service(name):
            self.manager.stop_service(self, name, self.remove)
            self.success("Successfully stopped {} service".format(name))

        self.run_list([
            'zimagi-scheduler',
            'zimagi-worker'
        ], stop_service)
