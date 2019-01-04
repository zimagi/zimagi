from systems.command import types, mixins


class ListCommand(
    mixins.op.ListMixin,
    mixins.data.ProjectMixin,
    types.ProjectActionCommand
):
    def get_description(self, overview):
        if overview:
            return """list projects in current environment

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """list projects in current environment
                      
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
        self.parse_project_reference(True)

    def exec(self):
        self.exec_list(self._project,
            'name',
            'environment',
            'type',
            'remote',
            'path',
            name__in = [ project.name for project in self.projects ]
        )
