
class ConfigMixin(object):

    def get_configs(self):
        facade = self.command.facade(self.command._config)
        return self.command.get_instances(facade)        

    def get_config(self, name):
        facade = self.command.facade(self.command._config)
        return self.command.get_instance(facade, name, required = False)        


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

    def export_configs(self):
        index = {}
        for config in self.get_configs():
            index[config.name] = config.value
        
        self.data['config'] = index
