from systems.command.index import Command


class Action(Command('module.sync')):

    def exec(self):
        self.silent_data('modules', self.db.save('module', encrypted = False))

    def postprocess(self, result):
        self.db.load(result.get_named_data('modules'), encrypted = False)
        for module in self.get_instances(self._module):
            module.provider.update()

        self.exec_local('module install')
        self.success('Modules successfully synced from remote environment')
