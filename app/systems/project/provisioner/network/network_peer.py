
class NetworkPeerMixin(object):

    def get_network_peers(self):
        facade = self.command.facade(self.command._network_peer)
        return self.command.get_instances(facade)


    def ensure_network_peers(self):
        def process(name, state):
            self.ensure_network_peer(name, self.data['network-peer'][name])
        
        if self.include('network-peer') and 'network-peer' in self.data:
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


    def export_network_peers(self):
        def describe(network_peer):
            networks = []
            for peer in network_peer.peers.all():
                networks.append(peer.name)

            return { 
                'provider': network_peer.type,
                'networks': networks
            }
        
        if self.include('network-peer'):
            self._export('network-peer', self.get_network_peers(), describe, use_config = False)


    def destroy_network_peers(self):
        def process(name, state):
            self.destroy_network_peer(name, self.data['network-peer'][name])
        
        if self.include('network-peer') and 'network-peer' in self.data:
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
