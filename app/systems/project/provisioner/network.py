from systems.command.base import AppOptions
from utility.data import ensure_list


class NetworkProvisionerMixin(object):

    def get_network(self, name):
        return self.command.facade(self.command._network).retrieve(name)        

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


    def get_subnet(self, network, name):
        facade = self.command.facade(self.command._subnet)
        facade.set_scope(self.get_network(network))
        return facade.retrieve(name)

    def ensure_subnets(self):
        def process(name, state):
            self.ensure_subnet(name, self.data['subnet'][name])
        
        if 'subnet' in self.data:
            self.command.run_list(self.data['subnet'].keys(), process)
  
    def ensure_subnet(self, name, config):
        network = config.pop('network', None)

        if network is None:
            self.command.error("Subnet {} requires 'network' field".format(name))

        def process(network, state):
            if self.get_subnet(network, name):
                command = 'subnet update'
            else:
                command = 'subnet add'
        
            self.command.exec_local(command, { 
                'network_name': network,
                'subnet_name': name, 
                'subnet_fields': config
            })
        
        collection = AppOptions(self.command)
        self.command.run_list(ensure_list(collection.add('network', network)), process)


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
        if isinstance(config, dict):
            provider = config.pop('provider', name)
            peers = config.pop('networks')
        else:
            provider = name
            peers = config
        
        self.command.exec_local('network peers', { 
            'network_provider_name': provider,
            'network_peer_name': name,
            'clear': True,
            'force': True
        })

    def destroy_subnets(self):
        def process(name, state):
            self.destroy_subnet(name, self.data['subnet'][name])
        
        if 'subnet' in self.data:
            self.command.run_list(self.data['subnet'].keys(), process)
  
    def destroy_subnet(self, name, config):
        network = config.pop('network', None)

        if network is None:
            self.command.error("Subnet {} requires valid 'network' field".format(name))

        def process(network, state):
            if self.get_network(network):
                self.command.exec_local('subnet rm', { 
                    'network_name': network,
                    'subnet_name': name,
                    'force': True
                })
        
        collection = AppOptions(self.command)
        self.command.run_list(ensure_list(collection.add('network', network)), process)
