
class NetworkProvisionerMixin(object):

    def get_network(self, name):
        return self.command.get_instance(self.command._network, name, required = False)        
  

    def ensure_networks(self):
        if 'network' in self.data:
            for name, config in self.data['network'].items():
                self.ensure_network(name, config)
  
    def ensure_network(self, name, config):
        provider = config.pop('provider', None)

        if provider is None:
            self.command.error("Network {} requires 'provider' field".format(name))
        
        options = { 'network_name': name, 'network_fields': config }
        if self.get_network(name):
            command = 'network update'
        else:
            command = 'network add'
            options['network_provider_name'] = provider
        
        self.command.exec_local(command, options)


    def destroy_networks(self):
        if 'network' in self.data:
            for name, config in self.data['network'].items():
                self.destroy_network(name)

    def destroy_network(self, name):
        self.command.exec_local('network rm', { 
            'network_name': name,
            'force': True
        })
