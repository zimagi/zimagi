
class NetworkMixin(object):

    def get_networks(self):
        facade = self.command.facade(self.command._network)
        return self.command.get_instances(facade)


    def ensure_networks(self):
        def process(name, state):
            self.ensure_network(name, self.data['network'][name])
        
        if self.include('network') and 'network' in self.data:
            self.command.run_list(self.data['network'].keys(), process)
  
    def ensure_network(self, name, config):
        provider = config.pop('provider', None)

        if provider is None:
            self.command.error("Network {} requires 'provider' field".format(name))
        
        self.command.exec_local('network save', {
            'network_provider_name': provider,
            'network_name': name, 
            'network_fields': config 
        })


    def export_networks(self):
        def describe(network):
            return { 'provider': network.type }
        
        if self.include('network'):
            self._export('network', self.get_networks(), describe)


    def destroy_networks(self):
        def process(name, state):
            self.destroy_network(name)
        
        if self.include('network') and 'network' in self.data:
            self.command.run_list(self.data['network'].keys(), process)

    def destroy_network(self, name):
        self.command.exec_local('network rm', { 
            'network_name': name,
            'force': True
        })
