from systems.command.base import AppOptions
from utility.data import ensure_list


class SubnetMixin(object):

    def get_subnets(self):
        facade = self.command.facade(self.command._subnet)
        return self.command.get_instances(facade)


    def ensure_subnets(self):
        def process(name, state):
            self.ensure_subnet(name, self.data['subnet'][name])
        
        if self.include('subnet') and 'subnet' in self.data:
            self.command.run_list(self.data['subnet'].keys(), process)
  
    def ensure_subnet(self, name, config):
        network = config.pop('network', None)

        if network is None:
            self.command.error("Subnet {} requires 'network' field".format(name))

        def process(network, state):
            self.command.exec_local('subnet save', { 
                'network_name': network,
                'subnet_name': name, 
                'subnet_fields': config
            })
        
        collection = AppOptions(self.command)
        self.command.run_list(ensure_list(collection.add('network', network)), process)


    def export_subnets(self):
        def describe(subnet):
            return { 'network': subnet.network.name }
        
        if self.include('subnet'):
            self._export('subnet', self.get_subnets(), describe)


    def destroy_subnets(self):
        def process(name, state):
            self.destroy_subnet(name, self.data['subnet'][name])
        
        if self.include('subnet') and 'subnet' in self.data:
            self.command.run_list(self.data['subnet'].keys(), process)
  
    def destroy_subnet(self, name, config):
        network = config.pop('network', None)

        if network is None:
            self.command.error("Subnet {} requires valid 'network' field".format(name))

        def process(network, state):
            self.command.exec_local('subnet rm', { 
                'network_name': network,
                'subnet_name': name,
                'force': True
            })
        
        collection = AppOptions(self.command)
        self.command.run_list(ensure_list(collection.add('network', network)), process)
