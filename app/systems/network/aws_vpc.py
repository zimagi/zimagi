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


    def create_provider_network(self, network):
        ec2 = self.ec2(network.config['region'])

        network.cidr = self._get_cidr(network.config, self.command.networks)
        if not network.cidr:
            self.command.error("No available network cidr matches. Try another cidr")
        
        response = ec2.create_vpc(
            CidrBlock = network.cidr,
            InstanceTenancy = network.config['tenancy']
        )
        network.config['vpc_id'] = response['Vpc']['VpcId']

        ec2.modify_vpc_attribute(
            VpcId = network.config['vpc_id'],
            EnableDnsSupport = {
                'Value': True
            }
        )
        ec2.modify_vpc_attribute(
            VpcId = network.config['vpc_id'],
            EnableDnsHostnames = {
                'Value': True
            }
        )
        response = ec2.create_internet_gateway()
        network.config['ig_id'] = response['InternetGateway']['InternetGatewayId']

        ec2.attach_internet_gateway(
            InternetGatewayId = network.config['ig_id'],
            VpcId = network.config['vpc_id']
        )

        response = ec2.create_route_table(
            VpcId = network.config['vpc_id']
        )
        network.config['route_table_id'] = response['RouteTable']['RouteTableId']

        ec2.create_route(
            DestinationCidrBlock = '0.0.0.0/0',
            GatewayId = network.config['ig_id'],
            RouteTableId = network.config['route_table_id']
        )

    def destroy_provider_network(self):
        ec2 = self.ec2(self.network.config['region'])
        ec2.delete_route_table(
            RouteTableId = self.network.config['route_table_id']
        )
        ec2.delete_internet_gateway(
            InternetGatewayId = self.network.config['ig_id']
        )
        ec2.delete_vpc(
            VpcId = self.network.config['vpc_id']
        )       


    def create_provider_subnet(self, subnet):
        ec2 = self.ec2(self.network.config['region'])

        subnet.config['cidr_base'] = self.network.cidr
        subnet.cidr = self._get_cidr(subnet.config, self.command.subnets)
        if not subnet.cidr:
            self.command.error("No available subnet cidr matches. Try another cidr")

        if not subnet.config['zone']:
            zones = self.zones(self.ec2, self.network.config['region'])
            subnet.config['zone'] = zones[random.randint(0, len(zones) - 1)]
   
        response = ec2.create_subnet(
            VpcId = self.network.config['vpc_id'],
            AvailabilityZone = subnet.config['zone'],
            CidrBlock = subnet.cidr
        )
        subnet.config['subnet_id'] = response['Subnet']['SubnetId']

        ec2.associate_route_table(
            RouteTableId = self.network.config['route_table_id'],
            SubnetId = subnet.config['subnet_id']
        )

        if bool(subnet.config['public_ip']):
            ec2.modify_subnet_attribute(
                SubnetId = subnet.config['subnet_id'],
                MapPublicIpOnLaunch = {
                    'Value': True
                } 
            )

    def destroy_provider_subnet(self, subnet):
        ec2 = self.ec2(self.network.config['region'])
        ec2.delete_subnet(
            SubnetId = subnet.config['subnet_id']
        )


    def create_provider_firewall(self, name, firewall):
        ec2 = self.ec2(self.network.config['region'])
        description = firewall.config['description'] if firewall.config['description'] else name

        response = ec2.create_security_group(
            VpcId = self.network.config['vpc_id'],
            GroupName = name,
            Description = description
        )
        firewall.config['sgroup_id'] = response['GroupId']

    def destroy_provider_firewall(self, firewall):
        ec2 = self.ec2(self.network.config['region'])
        ec2.delete_security_group(
            GroupId = firewall.config['sgroup_id']
        )


    def create_provider_firewall_rule(self, firewall, name, rule):
        rule.type = rule.config['type'].lower()
        rule.protocol = rule.config['protocol'].lower()
        rule.from_port = rule.config['from_port']
        rule.to_port = rule.config['to_port']

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

        if rule.config['cidrs']:
            rule.cidrs = [str(self._parse_cidr(x.strip())) for x in rule.config['cidrs'].split(',')]
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

    def destroy_provider_firewall_rule(self, firewall, rule):
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
