from systems.command.base import command_list
from systems.command import types, mixins, factory


class Command(
    mixins.data.ServerMixin, 
    types.ProjectActionCommand
):
    def get_command_name(self):
        return 'task'

    def groups_allowed(self):
        return False # Access control via task definitions

    def parse(self):
        self.parse_project_name()
        self.parse_server_reference('--servers')
        self.parse_task_name()        
        self.parse_task_params(True)

    def exec(self):
        self.project.provider.exec_task(
            self.task_name,
            self.servers,
            self.task_params
        )
