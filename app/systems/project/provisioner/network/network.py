
class NetworkMixin(object):

    def ensure_network(self, name, config):
        provider = self.pop_value('provider', config)
        groups = self.pop_values('group_names', config)

        if not provider:
            self.command.error("Network {} requires 'provider' field".format(name))

        self.command.exec_local('network save', {
            'network_provider_name': provider,
            'network_name': name,
            'network_fields': config,
            'group_names': groups
        })

    def describe_network(self, network):
        return { 'provider': network.type }

    def destroy_network(self, name, config):
        self.command.exec_local('network rm', {
            'network_name': name,
            'force': True
        })
