from systems.command.base import AppOptions
from utility.data import ensure_list


class FirewallMixin(object):

    def get_firewalls(self):
        facade = self.command.facade(self.command._firewall)
        return self.command.get_instances(facade)


    def ensure_firewalls(self):
        def process(name, state):
            self.ensure_firewall(name, self.data['firewall'][name])
        
        if self.include('firewall') and 'firewall' in self.data:
            self.command.run_list(self.data['firewall'].keys(), process)
  
    def ensure_firewall(self, name, config):
        collection = AppOptions(self.command)
        network = config.pop('network', None)
        rules = config.pop('rules', None)

        if network is None:
            self.command.error("Firewall {} requires 'network' field".format(name))

        if rules is None:
            self.command.error("Firewall {} requires 'rules' field defined".format(name))

        def process_firewall(network, state):
            self.command.exec_local('firewall save', { 
                'network_name': network,
                'firewall_name': name, 
                'firewall_fields': config
            })
            def process_rule(rule, state):
                self.command.exec_local('firewall rule save', { 
                    'network_name': network,
                    'firewall_name': name,
                    'firewall_rule_name': rule, 
                    'firewall_rule_fields': rules[rule]
                })
            self.command.run_list(rules.keys(), process_rule)

        self.command.run_list(ensure_list(collection.add('network', network)), process_firewall)


    def export_firewalls(self):
        def describe(firewall):
            config = { 'network': firewall.network.name }
            rules = {}

            for rule in firewall.rules.all():
                rules[rule.name] = self.get_variables(rule)

            config['rules'] = rules
            return config
        
        if self.include('firewall'):
            self._export('firewall', self.get_firewalls(), describe)


    def destroy_firewalls(self):
        def process(name, state):
            self.destroy_firewall(name, self.data['firewall'][name])
        
        if self.include('firewall') and 'firewall' in self.data:
            self.command.run_list(self.data['firewall'].keys(), process)
  
    def destroy_firewall(self, name, config):
        collection = AppOptions(self.command)
        network = config.pop('network', None)
        rules = config.pop('rules', None)

        if network is None:
            self.command.error("Firewall {} requires 'network' field".format(name))

        if rules is None:
            self.command.error("Firewall {} requires 'rules' field defined".format(name))

        def process_firewall(network, state):
            def process_rule(rule, state):
                self.command.exec_local('firewall rule rm', { 
                    'network_name': network,
                    'firewall_name': name,
                    'firewall_rule_name': rule,
                    'force': True
                })
            
            self.command.run_list(rules.keys(), process_rule)
            self.command.exec_local('firewall rm', { 
                'network_name': network,
                'firewall_name': name,
                'force': True
            })
        
        self.command.run_list(ensure_list(collection.add('network', network)), process_firewall)
