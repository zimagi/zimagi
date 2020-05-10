from systems.command.types import module


class Command(
    module.ModuleActionCommand
):
    def get_priority(self):
        return -100

    def groups_allowed(self):
        return False # Access control via task definitions

    def parse(self):
        self.parse_module_name()
        self.parse_task_name()
        self.parse_task_fields(True)

    def exec(self):
        self.module.provider.exec_task(
            self.task_name,
            self.task_fields
        )
