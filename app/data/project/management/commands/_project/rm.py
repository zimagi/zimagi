from systems.command import types, mixins


class RemoveCommand(
    mixins.op.RemoveMixin,
    mixins.data.ProjectMixin, 
    types.ProjectActionCommand
):
    def get_description(self, overview):
        if overview:
            return """remove an existing project in current environment

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """remove an existing project in current environment
                      
Etiam mattis iaculis felis eu pharetra. Nulla facilisi. 
Duis placerat pulvinar urna et elementum. Mauris enim risus, 
mattis vel risus quis, imperdiet convallis felis. Donec iaculis 
tristique diam eget rutrum.

Etiam sit amet mollis lacus. Nulla pretium, neque id porta feugiat, 
erat sapien sollicitudin tellus, vel fermentum quam purus non sem. 
Mauris venenatis eleifend nulla, ac facilisis nulla efficitur sed. 
Etiam a ipsum odio. Curabitur magna mi, ornare sit amet nulla at, 
scelerisque tristique leo. Curabitur ut faucibus leo, non tincidunt 
velit. Aenean sit amet consequat mauris.
"""
    def parse(self):
        self.parse_project_reference()

    def confirm(self):
        self.confirmation()       

    def exec(self):
        def remove_project(project, state):
            project.project_provider.destroy_project()
            self.exec_rm(self._project, project.name)

        self.run_list(self.projects, remove_project)
