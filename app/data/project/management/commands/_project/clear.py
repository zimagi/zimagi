from systems.command import types, mixins


class ClearCommand(
    mixins.op.RemoveMixin,
    types.ProjectActionCommand
):
    def get_description(self, overview):
        if overview:
            return """clear all existing projects in current environment

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """clear all existing projects in current environment
                      
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
    def confirm(self):
        self.confirmation()       

    def exec(self):
        def remove_project(project, state):
            self.exec_local('project rm', {
                'project_reference': "name>{}".format(project.name)
            })
        self.run_list(self.projects, remove_project)
