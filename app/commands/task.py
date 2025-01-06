from systems.commands.index import Command


class Task(Command("task")):
    def exec(self):
        self.module.provider.exec_task(self.task_key, self.task_fields)
