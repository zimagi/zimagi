
class ProjectProvisionerMixin(object):

    def get_project(self, name):
        return self.command.get_instance(self.command._project, name, required = False)        


    def ensure_projects(self):
        def process(name, state):
            self.ensure_project(name, self.data['project'][name])
        
        if 'project' in self.data:
            self.command.run_list(self.data['project'].keys(), process)
    
    def ensure_project(self, name, config):
        provider = config.pop('provider', None)

        if provider is None:
            self.command.error("Project {} requires 'provider' field".format(name))
        
        options = { 'project_fields': config }
        if self.get_project(name):
            command = 'project update'
            options['project_reference'] = "name>{}".format(name)
        else:
            command = 'project add'
            options['project_provider_name'] = provider
            options['project_name'] = name
        
        self.command.exec_local(command, options)


    def destroy_projects(self):
        def process(name, state):
            self.destroy_project(name)
        
        if 'project' in self.data:
            self.command.run_list(self.data['project'].keys(), process)

    def destroy_project(self, name):
        self.command.exec_local('project rm', { 
            'project_reference': "name>{}".format(name),
            'force': True
        })
