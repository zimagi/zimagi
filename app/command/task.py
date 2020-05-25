from systems.command.index import Command


class Action(Command('task')):

    def exec(self):
        self.module.provider.exec_task(
            self.task_name,
            self.task_fields
        )
