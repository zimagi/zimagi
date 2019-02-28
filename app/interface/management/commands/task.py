from systems.command import types, mixins


class Command(
    mixins.data.ServerMixin, 
    types.ProjectActionCommand
):
    def get_command_name(self):
        return 'task'

    def get_priority(self):
        return -100

    def groups_allowed(self):
        return False # Access control via task definitions

    def parse(self):
        self.parse_server_search('--servers')
        self.parse_project_name()        
        self.parse_task_name()        
        self.parse_task_params(True)

    def exec(self):
        self.project.provider.exec_task(
            self.task_name,
            self.server_instances,
            self.task_params
        )
