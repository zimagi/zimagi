
class ProjectMixin(object):

    def get_project(self, name):
        facade = self.command.facade(self.command._project)
        return self.command.get_instance(facade, name, required = False)

    def ensure_project(self, name, config):
        provider = config.pop('provider', None)
        if provider is None:
            self.command.error("Project {} requires 'provider' field".format(name))

        self.command.exec_local('project save', {
            'project_provider_name': provider,
            'project_name': name,
            'project_fields': config
        })

    def describe_project(self, project):
        return { 'provider': project.type }

    def destroy_project(self, name, config):
        self.command.exec_local('project rm', {
            'project_name': name,
            'force': True
        })
