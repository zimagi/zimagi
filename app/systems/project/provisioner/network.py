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


    def get_firewall(self, network, name):
        facade = self.command.facade(self.command._firewall)
        facade.set_scope(self.get_network(network))
        return facade.retrieve(name)

    def get_firewall_rule(self, network, firewall, name):
        facade = self.command.facade(self.command._firewall_rule)
        facade.set_scope(self.get_firewall(network, firewall))
        return facade.retrieve(name)

    def ensure_firewalls(self):
        def process(name, state):
            self.ensure_firewall(name, self.data['firewall'][name])
        
        if 'firewall' in self.data:
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
            if self.get_firewall(network, name):
                command = 'firewall update'
            else:
                command = 'firewall add'
        
            self.command.exec_local(command, { 
                'network_name': network,
                'firewall_name': name, 
                'firewall_fields': config
            })

            def process_rule(rule, state):
                if self.get_firewall_rule(network, name, rule):
                    command = 'firewall rule update'
                else:
                    command = 'firewall rule add'
        
                self.command.exec_local(command, { 
                    'network_name': network,
                    'firewall_name': name,
                    'firewall_rule_name': rule, 
                    'firewall_rule_fields': rules[rule]
                })
            self.command.run_list(rules.keys(), process_rule)

        self.command.run_list(ensure_list(collection.add('network', network)), process_firewall)


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


    def destroy_firewalls(self):
        def process(name, state):
            self.destroy_firewall(name, self.data['firewall'][name])
        
        if 'firewall' in self.data:
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
