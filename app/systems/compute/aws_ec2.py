from django.conf import settings

from utility import cloud
from .base import BaseComputeProvider

import random
import time
import json


class AWSEC2(cloud.AWSServiceMixin, BaseComputeProvider):

    def provider_config(self):
        self.requirement('vpc', help = 'AWS VPC identifier (ex: vpc-20810ee6)')
        self.requirement('cidr', None, help = 'AWS subnet CIDR address (within VPC CIDR)')
        
        self.option('count', 1, help = 'AWS instance count')

        self.option('region', 'us-east-1', self.validate_region, self.ec2, help = 'AWS region name')
        self.option('zone', None, self.validate_zone, self.ec2, help = 'AWS availability zone (default random)')
        self.option('ami', 'ami-0d2505740b82f7948', help = 'AWS image name') # Ubuntu 18.04LTS hvm:ebs-ssd us-east-1
        self.option('type', 't2.micro', help = 'AWS instance type')
        
        self.option('sgroups', None, help = 'One or more AWS security group ids')
        self.option('monitoring', False, help = 'AWS monitoring enabled?')

        self.option('data_device', '/dev/xvdb', help = 'Server data drive device')
        self.option('ebs_optimized', False, help = 'AWS EBS obtimized server?')
        self.option('ebs_type', 'gp2', help = 'AWS data drive EBS type')
        self.option('ebs_size', 10, help = 'AWS data drive EBS volume size (GB)')
        self.option('ebs_iops', None, help = 'AWS data drive EBS provisioned IOPS')
        
        self.option('user', 'ubuntu', help = 'Server SSH user')
        self.option('password', None, help = 'Password of server user')


    def initialize_servers(self):
        ec2 = self.ec2(self.config['region'])

        self.config['list'] = range(0, int(self.config['count']))

        if not self.config['zone']:
            zones = self.zones(self.ec2, self.config['region'])
            self.config['zone'] = zones[random.randint(0, len(zones) - 1)]

        self.config['subnet_id'] = self._create_subnet(ec2, 
            self.config['vpc'], 
            self.config['zone'],
            self.config['cidr']
        )

        self.config['sgroup_id'] = self._create_security_group(ec2, 
            self.config['vpc'], 
            'CE server management interface: {}'.format(self.create_token())
        )
        self._add_ingress_rules(ec2, self.config['sgroup_id'], [
            self.ingress_rule(22, cidrs = "{}/32".format(self.get_external_ip()))
        ])


    def create_server(self, index, server):
        ec2 = self.ec2(server.region)

        try:
            key_name, private_key = self._create_keypair(ec2)

            options = {
                'MinCount': 1,
                'MaxCount': 1,
                'InstanceType': server.config['type'],
                'ImageId': server.config['ami'],
                'SubnetId': server.config['subnet_id'],
                'Placement': {
                    'AvailabilityZone': server.config['zone']
                },
                'SecurityGroupIds': [ server.config['sgroup_id'] ],
                'Monitoring': {
                    'Enabled': server.config['monitoring']
                },
                'KeyName': key_name,
                'EbsOptimized': server.config['ebs_optimized'],
                'BlockDeviceMappings': [
                    {
                        'DeviceName': server.config['data_device'],
                        'Ebs': {
                            'DeleteOnTermination': True,
                            'VolumeType': server.config['ebs_type'],
                            'VolumeSize': server.config['ebs_size']
                        }
                    }
                ]
            }
            if server.config['sgroups']:
                if isinstance(server.config['sgroups'], str):
                    options['SecurityGroupIds'].append(server.config['sgroups'])
                else:
                    options['SecurityGroupIds'].extend(server.config['sgroups'])

            if server.config['ebs_iops']:
                options['BlockDeviceMappings'][0]['Ebs']['Iops'] = server.config['ebs_iops']

            server.private_key = private_key
            server.name = self._init_server(ec2, options)
        
            instance = self._get_server(ec2, server.name)
            server.zone = server.config['zone']
            server.ip = instance['PublicIpAddress']

        finally:
            self._delete_keypair(ec2, key_name)

        if not self.check_ssh(server = server):
            self.command.warning("Cleaning up AWS instance {} due to communication failure... (check security groups)".format(server.name))
            self.destroy_server(server = server)
            self.command.error("Can not establish SSH connection to: {}".format(server))


    def destroy_server(self, strict = True, server = None):
        if not self.server and not server:
            self.command.error("Destroying server requires a valid server instance given to provider on initialization")
        if not server:
            server = self.server

        self.command.data("Destroying AWS instance", server.name)
        ec2 = self.ec2(server.region)
        self._destroy_servers(ec2, server.name, strict = strict)


    def _init_server(self, ec2, options):
        result = ec2.run_instances(**options)
        return result['Instances'][0]['InstanceId']

    def _destroy_servers(self, ec2, instance_ids, strict = True):
        try:
            instance_ids = [instance_ids] if not isinstance(instance_ids, (list, tuple)) else instance_ids
            return ec2.terminate_instances(InstanceIds = instance_ids)
        except Exception as e:
            if strict:
                raise e
            self.command.warning(e)
      

    def _get_server(self, ec2, name, tries = 5, interval = 2):
        while True:
            try:
                result = ec2.describe_instances(InstanceIds = [name])
                instance = result['Reservations'][0]['Instances'][0]
            
                if instance['State']['Name'] != 'pending':
                    break
                
                time.sleep(interval)
            
            except Exception as e:
                if not tries:
                    self.command.error(e)
                
                time.sleep(interval)
                tries -= 1

        return instance


    def _get_keynames(self, ec2):
        key_names = []
        keypairs = ec2.describe_key_pairs()
        for keypair in keypairs['KeyPairs']:
            key_names.append(keypair['KeyName'])

        return key_names

    def _create_keypair(self, ec2):
        key_names = self._get_keynames(ec2)

        while True:
            key_name = "ce_{}".format(random.randint(1, 1000001))
            if key_name not in key_names:
                break
        
        self.command.data("Creating initial keypair", key_name, "keypair_create_{}".format(key_name))
        keypair = ec2.create_key_pair(KeyName = key_name)
        return (key_name, keypair['KeyMaterial'])

    def _delete_keypair(self, ec2, key_name):
        self.command.data("Deleting initial keypair", key_name, "keypair_delete_{}".format(key_name))
        return ec2.delete_key_pair(KeyName = key_name)
