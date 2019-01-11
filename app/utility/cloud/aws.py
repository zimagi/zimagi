
import boto3
import netaddr
import requests
import string
import random


class AWSIngressRule(object):

    def __init__(self, from_port, to_port = None, ip_protocol = 'tcp', cidrs = '0.0.0.0/0'):
        self.from_port = from_port
        self.to_port = to_port if to_port is not None else from_port
        self.ip_protocol = ip_protocol
        self.cidrs = [cidrs] if not isinstance(cidrs, (list, tuple)) else cidrs

    def export(self):
        data = {
            'FromPort': self.from_port,
            'ToPort': self.to_port,
            'IpProtocol': self.ip_protocol,
            'IpRanges': []    
        }
        for cidr in self.cidrs:
            data['IpRanges'].append({ 'CidrIp': cidr })

        return data


class AWSServiceMixin(object):

    def _init_session(self):
        if not getattr(self, 'session', None):
            try:
                access_key = self.command.required_config('aws_access_key').strip()
                secret_key = self.command.required_config('aws_secret_key').strip()
            except Exception:
                self.command.error("To use AWS provider you must have 'aws_access_key' and 'aws_secret_key' environment configurations; see: config set")

            self.session = boto3.Session(
                aws_access_key_id = access_key,
                aws_secret_access_key = secret_key
            )  

    def ec2(self, region = 'us-east-1'):
        self._init_session()
        return self.session.client('ec2', region_name = region)

    def efs(self, region = 'us-east-1'):
        self._init_session()
        return self.session.client('efs', region_name = region)


    def regions(self, service):
        if not getattr(self, '_regions', None):
            regions = service().describe_regions()
            self._regions = []

            for region in regions['Regions']:
                self._regions.append(region['RegionName'])

        return self._regions

    def validate_region(self, name, value, errors, service):
        regions = self.regions(service)
        
        if not value in regions:
            errors.append("Region '{}' is not available, consider: {}".format(value, ", ".join(regions)))

    def zones(self, service, region):
        if not getattr(self, '_zones', None) or region not in self._zones:
            self._zones = getattr(self, '_zones', {})
            self._zones[region] = []

            zones = service(region).describe_availability_zones()
        
            for zone in zones['AvailabilityZones']:
                if zone['State'] == 'available':
                    self._zones[region].append(zone['ZoneName'])
        
        return self._zones[region]

    def validate_zone(self, name, value, errors, service):
        if self.config['region']:
            zones = self.zones(service, self.config['region'])
        
            if not value in zones:
                errors.append("Zone '{}' is not available, consider: {}".format(value, ", ".join(zones)))
        else:
            errors.append("Region is required to validate availability zone")            


    def get_subnets(self, cidr, subnet_block_size):
        ip_space = netaddr.IPNetwork(cidr)
        return list(ip_space.subnet(subnet_block_size))

    def get_block_size(self, cidr):
        ip_space = netaddr.IPNetwork(cidr)
        return ip_space.prefixlen


    def _create_subnet(self, ec2, vpc, zone, subnet_cidr, public_ips = True):
        response = ec2.create_subnet(
            VpcId = vpc,
            AvailabilityZone = zone,
            CidrBlock = subnet_cidr
        )
        subnet_id = response['Subnet']['SubnetId']

        if public_ips:
            ec2.modify_subnet_attribute(
                SubnetId = subnet_id,
                MapPublicIpOnLaunch = {
                    'Value': True
                } 
            )
        
        return subnet_id

    def _create_security_group(self, ec2, vpc, name):
        response = ec2.create_security_group(
            VpcId = vpc,
            GroupName = name,
            Description = name
        )
        return response['GroupId']

    def _add_ingress_rules(self, ec2, sgroup_id, rules):
        permissions = []

        for rule in rules:
            permissions.append(rule.export())

        ec2.authorize_security_group_ingress(
            GroupId = sgroup_id,
            IpPermissions = permissions
        )

    @property
    def ingress_rule(self):
        return AWSIngressRule


    def get_external_ip(self):
        return requests.get('https://api.ipify.org').text


    def create_token(self):
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.SystemRandom().choice(chars) for _ in range(32))
