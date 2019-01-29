from django.conf import settings

from utility import cloud
from .base import BaseComputeProvider

import random
import time
import json


class AWSEC2(cloud.AWSServiceMixin, BaseComputeProvider):

    def provider_config(self, type = None):
        self.option('count', 1, help = 'AWS instance count')

        self.option('ami', 'ami-0d2505740b82f7948', help = 'AWS image name', config_name = 'aws_ec2_image') # Ubuntu 18.04LTS hvm:ebs-ssd us-east-1
        self.option('type', 't2.micro', help = 'AWS instance type', config_name = 'aws_ec2_type')
        
        self.option('monitoring', 'False', help = 'AWS monitoring enabled?', config_name = 'aws_ec2_monitoring')

        self.option('data_device', '/dev/xvdb', help = 'Server data drive device', config_name = 'aws_ec2_data_device')
        self.option('ebs_optimized', 'False', help = 'AWS EBS obtimized server?', config_name = 'aws_ec2_ebs_optimized')
        self.option('ebs_type', 'gp2', help = 'AWS data drive EBS type', config_name = 'aws_ec2_ebs_type')
        self.option('ebs_size', 10, help = 'AWS data drive EBS volume size (GB)', config_name = 'aws_ec2_ebs_size')
        self.option('ebs_iops', None, help = 'AWS data drive EBS provisioned IOPS', config_name = 'aws_ec2_ebs_size')
        
        self.option('user', 'ubuntu', help = 'Server SSH user', config_name = 'aws_ec2_user')


    def initialize_provider_servers(self):
        self.config['list'] = range(0, int(self.config['count']))


    def create_provider_server(self, index, server):
        if server.subnet.network.type != 'aws_vpc':
            self.command.error("AWS VPC network needed to create AWS compute instances")

        ec2 = self.ec2(server.subnet.network.config['region'])
        try:
            key_name, private_key = self._create_keypair(ec2)
            ssh_found = False

            for firewall in server.firewalls:
                if firewall.name == 'ssh':
                    ssh_found = True

            if not ssh_found:
                firewall = self.command.get_instance(self.command._firewall, 'ssh', required = False)
                if firewall:
                    server.firewalls.append(firewall)

            options = {
                'MinCount': 1,
                'MaxCount': 1,
                'InstanceType': server.config['type'],
                'ImageId': server.config['ami'],
                'SubnetId': server.subnet.config['subnet_id'],
                'Placement': {
                    'AvailabilityZone': server.subnet.config['zone']
                },
                'SecurityGroupIds': [],
                'Monitoring': {
                    'Enabled': json.loads(server.config['monitoring'].lower())
                },
                'KeyName': key_name,
                'EbsOptimized': json.loads(server.config['ebs_optimized'].lower()),
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
            if server.firewalls:
                sgroups = self._get_security_groups(server.firewalls)
                options['SecurityGroupIds'].extend(sgroups)

            options['SecurityGroupIds'] = list(set(options['SecurityGroupIds']))

            if server.config['ebs_iops']:
                options['BlockDeviceMappings'][0]['Ebs']['Iops'] = server.config['ebs_iops']

            server.private_key = private_key

            response = ec2.run_instances(**options)
            server.config['instance_id'] = response['Instances'][0]['InstanceId']
            server.name = self.create_server_name()

            instance = self._get_server(ec2, server.config['instance_id'])
            
            if server.subnet.config['public_ip']:
                server.ip = instance['PublicIpAddress']
            else:
                server.ip = instance['PrivateIpAddress']

        finally:
            self._delete_keypair(ec2, key_name)

        if not self.check_ssh(server = server, silent = True):
            self.command.warning("Cleaning up AWS instance {} due to communication failure... (check security groups)".format(server.config['instance_id']))
            ec2.terminate_instances(InstanceIds = [ server.config['instance_id'] ])
            self.command.error("Can not establish SSH connection to: {}".format(server))


    def update_provider_firewalls(self, firewalls):
        ec2 = self.ec2(self.server.subnet.network.config['region'])
        ec2.modify_instance_attribute(
            InstanceId = self.server.config['instance_id'],
            Groups = self._get_security_groups(firewalls)
        )


    def destroy_provider_server(self):
        ec2 = self.ec2(self.server.subnet.network.config['region'])
        ec2.terminate_instances(InstanceIds = [ self.server.config['instance_id'] ])
   

    def _get_server(self, ec2, name, tries = 5, interval = 2):
        while True:
            try:
                result = ec2.describe_instances(InstanceIds = [ name ])
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
        
        keypair = ec2.create_key_pair(KeyName = key_name)
        return (key_name, keypair['KeyMaterial'])

    def _delete_keypair(self, ec2, key_name):
        return ec2.delete_key_pair(KeyName = key_name)


    def _get_security_groups(self, firewalls):
        sgroups = []

        for firewall in firewalls:
            sgroups.append(firewall.config['sgroup_id'])                    
                
        return sgroups