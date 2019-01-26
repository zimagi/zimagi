from settings import Roles
from systems.command import types, mixins


class ListCommand(
    mixins.op.ListMixin,
    mixins.data.NetworkMixin,
    types.NetworkFirewallActionCommand
):
    def get_description(self, overview):
        if overview:
            return """list firewall rules in an environment firewall

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """list firewall rules in an environment firewall
                      
Etiam mattis iaculis felis eu pharetra. Nulla facilisi. 
Duis placerat pulvinar urna et elementum. Mauris enim risus, 
mattis vel risus quis, imperdiet convallis felis. Donec iaculis 
tristique diam eget rutrum.

Etiam sit amet mollis lacus. Nulla pretium, neque id porta feugiat, 
erat sapien sollicitudin tellus, vel fermentum quam purus non sem. 
Mauris venenatis eleifend nulla, ac facilisis nulla efficitur sed. 
Etiam a ipsum odio. Curabitur magna mi, ornare sit amet nulla at, 
scelerisque tristique leo. Curabitur ut faucibus leo, non tincidunt 
velit. Aenean sit amet consequat mauris.
"""
    def parse(self):
        self.parse_firewall_name(True)

    def exec(self):
        def process(op, info, key_index):
            if op == 'label':
                info.extend([
                    'rule',
                    'network',
                    'type', 
                    'from_port', 
                    'to_port', 
                    'protocol',
                    'cidrs'
                ])
            else:
                rule_names = []
                rule_networks = []
                rule_types = []
                rule_from_ports = []
                rule_to_ports = []
                rule_protocols = []
                rule_cidrs = []

                for rule in self._firewall_rule.query(
                    firewall__name = info[key_index]
                ):
                    rule_names.append(rule.name)
                    rule_networks.append(rule.firewall.network.name)
                    rule_types.append(rule.type)
                    rule_from_ports.append(str(rule.from_port))
                    rule_to_ports.append(str(rule.to_port))
                    rule_protocols.append(rule.protocol)
                    rule_cidrs.append(",".join(rule.cidrs))
                    
                info.append("\n".join(rule_names))
                info.append("\n".join(rule_networks))
                info.append("\n".join(rule_types))
                info.append("\n".join(rule_from_ports))
                info.append("\n".join(rule_to_ports))
                info.append("\n".join(rule_protocols))
                info.append("\n".join(rule_cidrs))

        if self.firewall_name:
            self._firewall_rule.set_scope(self.firewall)
            self.exec_list(self._firewall_rule,
                'name',
                'firewall__name',
                'firewall__network__name',
                'type',
                'from_port',
                'to_port',
                'protocol',
                '_cidrs'
            )
        else:
            self.exec_processed_sectioned_list(self._firewall, process, 'name')
