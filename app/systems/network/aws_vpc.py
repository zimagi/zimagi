from django.conf import settings

from utility import cloud
from .base import BaseNetworkProvider

import random


class AWSVPC(cloud.AWSServiceMixin, BaseNetworkProvider):

    def provider_config(self, type = None):
        if type:
            if type == 'network':
                self.option('cidr', None, help = 'AWS VPC IPv4 CIDR address (between /16 and /28)')
                self.option('cidr_base', '10/8', help = 'AWS VPC IPv4 root CIDR address (not used if "cidr" option specified)')
                self.option('cidr_prefix', '16', help = 'AWS VPC IPv4 CIDR address prefix size (not used if "cidr" option specified)')
                self.option('region', 'us-east-1', self.validate_region, self.ec2, help = 'AWS region name', config_name = 'aws_region')
                self.option('tenancy', 'default', help = 'AWS VPC instance tenancy (default | dedicated)', config_name = 'aws_vpc_tenancy')
            
            elif type == 'subnet':
                self.option('cidr', None, help = 'AWS VPC IPv4 CIDR address (between /16 and /28)')
                self.option('cidr_prefix', '24', help = 'AWS VPC IPv4 CIDR address prefix size (not used if "cidr" option specified)')
                self.option('zone', None, self.validate_zone, self.ec2, help = 'AWS availability zone (default random)', config_name = 'aws_zone')
                self.option('public_ip', True, help = 'Enable public IP addresses for instances in subnet')
            
            elif type == 'firewall':
                self.option('description', None, help = 'AWS security group description')
            
            elif type == 'firewall_rule':
                self.option('type', 'ingress', help = 'AWS security group rule type (ingress | egress)')
                self.option('protocol', 'tcp', help = 'AWS security group rule protocol (tcp | udp | icmp)')
                self.option('from_port', None, help = 'AWS security group rule from port (at least one "from" or "to" port must be specified)')
                self.option('to_port', None, help = 'AWS security group rule to port (at least one "from" or "to" port must be specified)')
                self.option('cidrs', None, help = 'AWS security group rule applicable CIDRs', config_name = 'aws_sgroup_cidrs')
 
            else:
                self.command.error("Network option type {} is unsupported in AWS VPC network provider".format(type))
        else:
            self.command.error("Network option type must be specified to use AWS VPC network provider")


    def initialize_network(self, network):
        ec2 = self.ec2(self.config['region'])

        network.cidr = self._get_cidr(self.config, self.command.networks)
        if not network.cidr:
            self.command.error("No available network cidr matches. Try another cidr")
        
        response = ec2.create_vpc(
            CidrBlock = network.cidr,
            InstanceTenancy = self.config['tenancy']
        )
        self.config['vpc_id'] = response['Vpc']['VpcId']

    def destroy_network(self):
        if not self.network:
            self.command.error("Destroying network requires a valid network instance given to provider on initialization")

        ec2 = self.ec2(self.network.config['region'])
        ec2.delete_vpc(
            VpcId = self.network.config['vpc_id']
        )        


    def initialize_subnet(self, subnet):
        if not self.network:
            self.command.error("Creating subnet requires a valid network instance given to provider on initialization")
        
        ec2 = self.ec2(self.network.config['region'])

        self.config['cidr_base'] = self.network.cidr
        subnet.cidr = self._get_cidr(self.config, self.command.subnets)
        if not subnet.cidr:
            self.command.error("No available subnet cidr matches. Try another cidr")

        if not self.config['zone']:
            zones = self.zones(self.ec2, self.network.config['region'])
            self.config['zone'] = zones[random.randint(0, len(zones) - 1)]
   
        response = ec2.create_subnet(
            VpcId = self.network.config['vpc_id'],
            AvailabilityZone = self.config['zone'],
            CidrBlock = subnet.cidr
        )
        self.config['subnet_id'] = response['Subnet']['SubnetId']

        if bool(self.config['public_ip']):
            ec2.modify_subnet_attribute(
                SubnetId = self.config['subnet_id'],
                MapPublicIpOnLaunch = {
                    'Value': True
                } 
            )

    def destroy_subnet(self, subnet):
        if not self.network:
            self.command.error("Destroying subnet requires a valid network instance given to provider on initialization")

        ec2 = self.ec2(self.network.config['region'])
        ec2.delete_subnet(
            SubnetId = subnet.config['subnet_id']
        )


    def initialize_firewall(self, name, firewall):
        if not self.network:
            self.command.error("Creating firewall ruleset requires a valid network instance given to provider on initialization")
        
        ec2 = self.ec2(self.network.config['region'])
        description = self.config['description'] if self.config['description'] else name

        response = ec2.create_security_group(
            VpcId = self.network.config['vpc_id'],
            GroupName = name,
            Description = description
        )
        self.config['sgroup_id'] = response['GroupId']

    def destroy_firewall(self, firewall):
        if not self.network:
            self.command.error("Destroying firewall ruleset requires a valid network instance given to provider on initialization")
        
        ec2 = self.ec2(self.network.config['region'])
        ec2.delete_security_group(
            GroupId = firewall.config['sgroup_id']
        )


    def initialize_firewall_rule(self, firewall, name, rule):
        if not self.network:
            self.command.error("Creating firewall rule requires a valid network instance given to provider on initialization")
        
        rule.type = self.config['type'].lower()
        rule.protocol = self.config['protocol'].lower()
        rule.from_port = self.config['from_port']
        rule.to_port = self.config['to_port']

        if rule.type not in ('ingress', 'egress'):
            self.command.error("Firewall rule type {} is not supported".format(rule.type))
        
        if rule.protocol not in ('tcp', 'udp', 'icmp'):
            self.command.error("Firewall rule protocol {} is not supported".format(rule.protocol))

        if not rule.from_port and not rule.to_port:
            self.command.error("Either 'from' and 'to' port must be specified to create firewall")

        if not rule.from_port:
            rule.from_port = rule.to_port
        if not rule.to_port:
            rule.to_port = rule.from_port

        if self.config['cidrs']:
            rule.cidrs = [str(self._parse_cidr(x.strip())) for x in self.config['cidrs'].split(',')]
        else:
            rule.cidrs = ['0.0.0.0/0']

        ec2 = self.ec2(self.network.config['region'])
        data = {
            'IpProtocol': rule.protocol,
            'FromPort': int(rule.from_port),
            'ToPort': int(rule.to_port),
            'IpRanges': []    
        }
        for cidr in rule.cidrs:
            data['IpRanges'].append({ 'CidrIp': cidr })

        if rule.type == 'ingress':
            ec2.authorize_security_group_ingress(
                GroupId = firewall.config['sgroup_id'],
                IpPermissions = [data]
            )
        elif rule.type == 'egress':
            ec2.authorize_security_group_egress(
                GroupId = firewall.config['sgroup_id'],
                IpPermissions = [data]
            )

    def destroy_firewall_rule(self, firewall, rule):
        if not self.network:
            self.command.error("Destroying firewall rule requires a valid network instance given to provider on initialization")
        
        ec2 = self.ec2(self.network.config['region'])
        data = {
            'IpProtocol': rule.protocol,
            'FromPort': rule.from_port,
            'ToPort': rule.to_port,
            'IpRanges': []    
        }
        for cidr in rule.cidrs:
            data['IpRanges'].append({ 'CidrIp': cidr })

        if rule.type == 'ingress':
            ec2.revoke_security_group_ingress(
                GroupId = firewall.config['sgroup_id'],
                IpPermissions = [data]
            )
        elif rule.type == 'egress':
            ec2.revoke_security_group_egress(
                GroupId = firewall.config['sgroup_id'],
                IpPermissions = [data]
            )
