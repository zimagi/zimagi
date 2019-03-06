
class ProjectMixin(object):

    def get_projects(self):
        facade = self.command.facade(self.command._project)
        projects = []
        for instance in self.command.get_instances(facade):
            if instance.type != 'internal':
                projects.append(instance)

        return projects

    def get_project(self, name):
        facade = self.command.facade(self.command._project)
        return self.command.get_instance(facade, name, required = False)


    def ensure_projects(self):
        def process(name, state):
            self.ensure_project(name, self.data['project'][name])

        if 'project' in self.data:
            self.command.run_list(self.data['project'].keys(), process)

    def ensure_project(self, name, config):
        provider = config.pop('provider', None)

        if provider is None:
            self.command.error("Project {} requires 'provider' field".format(name))

        self.command.exec_local('project save', {
            'project_provider_name': provider,
            'project_name': name,
            'project_fields': config
        })


    def export_projects(self):
        def describe(project):
            return { 'provider': project.type }

        self._export('project', self.get_projects(), describe)


    def destroy_projects(self):
        def process(name, state):
            self.destroy_project(name)

        if 'project' in self.data:
            self.command.run_list(self.data['project'].keys(), process)

    def destroy_project(self, name):
        self.command.exec_local('project rm', {
            'project_name': name,
            'force': True
        })
