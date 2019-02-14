
class ConfigProvisionerMixin(object):

    def get_config(self, name):
        return self.command.get_instance(self.command._config, name, required = False)        

    def set_config(self, params):
        def process(name, state):
            self.ensure_config(name, params[name])
        
        if params:
            self.command.run_list(params.keys(), process)


    def ensure_configs(self):
        def process(name, state):
            self.ensure_config(name, self.data['config'][name])
        
        if 'config' in self.data:
            self.command.run_list(self.data['config'].keys(), process)
    
    def ensure_config(self, name, value):
        self.command.exec_local('config set', {
            'config': name,
            'config_value': value
        })
