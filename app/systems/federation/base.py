
class BaseFederationProvider(providers.TerraformProvider):

    def __init__(self, name, command, instance = None):
        super().__init__(name, command, instance)
        self.provider_type = 'federation'
        self.provider_options = settings.FEDERATION_PROVIDERS


    def terraform_type(self):
        return 'federation'

    @property
    def facade(self):
        return self.command._federation

    def create(self, name, network_names):
        return super().create(name, { 'type': self.name }, networks = network_names)

    def update(self, network_names):
        return super().update({}, networks = network_names)

    def initialize_instance(self, instance, created):
        relations = instance.facade.get_relation_names()

        instance.save()

        self.update_related(instance, 'networks', self.command._network, relations['networks'])
        peer_map, peer_pairs = self._load_peers(list(instance.networks.all()))

        def process(pair_names):
            pair = (peer_map[pair_names[0]], peer_map[pair_names[1]])
            namespace = self._peer_namespace(pair)

            self.initialize_terraform(instance, created, pair)

            if self.test:
                self.terraform.plan(self.terraform_type(), instance, namespace)
            else:
                self.terraform.apply(self.terraform_type(), instance, namespace)

        self.command.run_list(peer_pairs, process)

    def finalize_instance(self, instance):
        peer_map, peer_pairs = self._load_peers(list(instance.networks.all()))

        def process(pair_names):
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
