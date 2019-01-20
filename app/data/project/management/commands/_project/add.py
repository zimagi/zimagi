from systems.command import types, mixins


class AddCommand(
    mixins.op.AddMixin,
    types.ProjectActionCommand
):
    def get_description(self, overview):
        if overview:
            return """add a new project in current environment

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """add a new project in current environment
                      
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
        self.parse_project_provider_name()
        self.parse_project_fields(True, self.get_provider('project', 'help').field_help)

    def exec(self):
        project = self.project_provider.create_project(self.project_fields)

        self.exec_add(self._project, project.name, {
            'config': project.config,
            'type': project.type,
            'remote': project.remote,
            'reference': project.reference
        })
