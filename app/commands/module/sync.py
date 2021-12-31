from systems.commands.index import Command


class Sync(Command('module.sync')):

    def exec(self):
        self.silent_data('modules', self.db.save('module', encrypted = False))

    def postprocess(self, response):
        self.db.load(response['modules'], encrypted = False)
        for module in self.get_instances(self._module):
            module.provider.update()

        self.exec_local('module install')
        self.success('Modules successfully synced from remote environment')
