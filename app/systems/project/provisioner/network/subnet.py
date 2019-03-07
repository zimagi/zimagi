from utility.data import ensure_list


class SubnetMixin(object):

    def ensure_subnet(self, name, config):
        groups = self.pop_values('group_names', config)

        def process(network):
            self.command.exec_local('subnet save', {
                'network_name': network,
                'subnet_name': name,
                'subnet_fields': config,
                'group_names': groups
            })
        if 'network' not in config:
            self.command.error("Subnet {} requires 'network' field".format(name))

        self.command.run_list(
            self.pop_values('network', config),
            process
        )

    def describe_subnet(self, subnet):
        return { 'network': subnet.network.name }
