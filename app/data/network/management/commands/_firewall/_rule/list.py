from settings import Roles
from systems.command import types, mixins


class ListCommand(
    mixins.op.ListMixin,
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
                    'Rule',
                    'Type', 
                    'From port', 
                    'To port', 
                    'Protocol',
                    'CIDRs'
                ])
            else:
                firewall = self.get_instance(self._firewall, info[key_index])
                rule_names = []
                rule_types = []
                rule_from_ports = []
                rule_to_ports = []
                rule_protocols = []
                rule_cidrs = []

                for rule in firewall.rules.all():
                    rule_names.append(rule.name)
                    rule_types.append(rule.type)
                    rule_from_ports.append(str(rule.from_port))
                    rule_to_ports.append(str(rule.to_port))
                    rule_protocols.append(rule.protocol)
                    rule_cidrs.append(",".join(rule.cidrs))
                    
                info.append("\n".join(rule_names))
                info.append("\n".join(rule_types))
                info.append("\n".join(rule_from_ports))
                info.append("\n".join(rule_to_ports))
                info.append("\n".join(rule_protocols))
                info.append("\n".join(rule_cidrs))

        if self.firewall_name:
            self.set_firewall_rule_scope()
            self.exec_list(self._firewall_rule,
                ('name', 'Name'),
                ('firewall__name', 'Firewall'),
                ('firewall__network__name', 'Network'),
                ('type', 'Type'),
                ('from_port', 'From port'),
                ('to_port', 'To port'),
                ('protocol', 'Protocol'),
                ('_cidrs', 'CIDRs')
            )
        else:
            self.exec_processed_sectioned_list(self._firewall, process, 
                ('name', 'Firewall'),
                ('network__name', 'Network')
            )
