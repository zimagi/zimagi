from systems.command import profile


class Provisioner(profile.BaseProvisioner):

    def priority(self):
        return 100

    def ensure(self, name, config):
        module = self.pop_value('module', config)
        task = self.pop_value('task', config)
        command = self.pop_value('command', config)

        if not task and not command:
            self.command.error("Provision {} requires 'task' or 'command' field".format(name))

        if command:
            self.exec(command, **config)
        else:
            self.exec('exec',
                module_name = module,
                task_name = task,
                task_fields = config
            )
