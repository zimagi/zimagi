
class ConfigProvisionerMixin(object):

    def get_config(self, name):
        return self.command.get_instance(self.command._config, name, required = False)        

    def set_config(self, params):
        for name, value in params.items():
            self.ensure_config(name, value)


    def ensure_configs(self):
        if 'config' in self.data:
            for name, value in self.data['config'].items():
                self.ensure_config(name, value)
    
    def ensure_config(self, name, value):
        self.command.exec_local('config set', {
            'config': name,
            'config_value': value
        })
