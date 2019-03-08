
class FirewallMixin(object):

    def ensure_firewall(self, name, config):
        networks = self.pop_values('network', config)
        rules = self.pop_info('rules', config)
        groups = self.pop_values('group_names', config)

        def process(network):
            self.command.exec_local('firewall save', {
                'network_name': network,
                'firewall_name': name,
                'firewall_fields': config,
                'group_names': groups
            })
            def process_rule(rule):
                self.command.exec_local('firewall rule save', {
                    'network_name': network,
                    'firewall_name': name,
                    'firewall_rule_name': rule,
                    'firewall_rule_fields': rules[rule]
                })
            self.command.run_list(rules.keys(), process_rule)

        if not networks:
            self.command.error("Firewall {} requires 'network' field".format(name))

        if not rules:
            self.command.error("Firewall {} requires 'rules' field defined".format(name))

        self.command.run_list(networks, process)


    def describe_firewall(self, firewall):
        return { 'network': firewall.network.name }
