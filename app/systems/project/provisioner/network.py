
class NetworkProvisionerMixin(object):

    def get_network(self, name):
        return self.command.get_instance(self.command._network, name, required = False)        
  

    def ensure_networks(self):
        def process(name, state):
            self.ensure_network(name, self.data['network'][name])
        
        if 'network' in self.data:
            self.command.run_list(self.data['network'].keys(), process)
  
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


    def ensure_network_peers(self):
        def process(name, state):
            self.ensure_network_peer(name, self.data['network-peer'][name])
        
        if 'network-peer' in self.data:
            self.command.run_list(self.data['network-peer'].keys(), process)

    def ensure_network_peer(self, name, config):
        if isinstance(config, dict):
            provider = config.pop('provider', name)
            peers = config.pop('networks')
        else:
            provider = name
            peers = config
        
        self.command.exec_local('network peers', { 
            'network_provider_name': provider,
            'network_peer_name': name,
            'network_names': peers
        })
    

    def destroy_networks(self):
        def process(name, state):
            self.destroy_network(name)
        
        if 'network' in self.data:
            self.command.run_list(self.data['network'].keys(), process)

    def destroy_network(self, name):
        self.command.exec_local('network rm', { 
            'network_name': name,
            'force': True
        })


    def destroy_network_peers(self):
        def process(name, state):
            self.destroy_network_peer(name, self.data['network-peer'][name])
        
        if 'network-peer' in self.data:
            self.command.run_list(self.data['network-peer'].keys(), process)

    def destroy_network_peer(self, name, config):
        if isinstance(config, list):
            provider = name
        else:
            provider = config.pop('provider', name)
        
        self.command.exec_local('network peers', { 
            'network_provider_name': provider,
            'network_peer_name': name,
            'clear': True
        })
