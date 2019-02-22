
class NetworkPeerProvider(providers.TerraformProvider):

    def __init__(self, name, command, instance = None):
        super().__init__(name, command, instance)
        self.provider_type = 'network'
        self.provider_options = settings.NETWORK_PROVIDERS

  
    def terraform_type(self):
        return 'network_peer'

    @property
    def facade(self):
        return self.command._network_peer

    def create(self, name, peer_names):
        return super().create(name, { 'type': self.name }, peers = peer_names)

    def update(self, peer_names):
        return super().update({}, peers = peer_names)
      
    def initialize_instance(self, instance, relations, created):
        instance.save()

        self.update_related(instance, 'peers', self.command._network, relations['peers'])
        peer_map, peer_pairs = self._load_peers(list(instance.peers.all()))

        def process(pair_names, state):
            pair = (peer_map[pair_names[0]], peer_map[pair_names[1]])
            namespace = self._peer_namespace(pair)

            self.initialize_terraform(instance, relations, created, pair)

            if self.test:
                self.terraform.plan(self.terraform_type(), instance, namespace)
            else:
                self.terraform.apply(self.terraform_type(), instance, namespace)

        self.command.run_list(peer_pairs, process)

    def finalize_instance(self, instance):
        peer_map, peer_pairs = self._load_peers(list(instance.peers.all()))

        def process(pair_names, state):
            pair = (peer_map[pair_names[0]], peer_map[pair_names[1]])
            
            self.finalize_terraform(instance, pair)
            self.terraform.destroy(
                self.terraform_type(), 
                instance, 
                self._peer_namespace(pair)
            )
        self.command.run_list(peer_pairs, process)


    def _load_peers(self, peers):
        peer_names = []
        peer_map = {}
        
        for peer in peers:
            peer_names.append(peer.name)
            peer_map[peer.name] = peer
        
        peer_pairs = list(itertools.combinations(peer_names, 2))
        return (peer_map, peer_pairs)

    def _peer_namespace(self, pair):
        return "{}.{}".format(pair[0].name, pair[1].name)
