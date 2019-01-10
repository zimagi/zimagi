from utility import cloud
from .base import BaseStorageProvider

import time
import string
import random
import json


class AWSEFS(cloud.AWSServiceMixin, BaseStorageProvider):

    def provider_config(self):
        self.requirement('vpc', help = 'AWS VPC identifier (ex: vpc-20810ee6)')
        self.option('cidr', None, help = 'AWS EFS subnet base network CIDR address (within VPC CIDR)')
        
        self.option('region', 'us-east-1', self.validate_region, self.efs, help = 'AWS region name')
        self.option('sgroups', None, help = 'One or more AWS security group ids')

        self.option('performance_mode', 'generalPurpose', help = 'AWS EFS performance mode (can also be: maxIO)')
        self.option('throughput_mode', 'bursting', help = 'AWS EFS throughput mode (can also be: provisioned)')
        self.option('provisioned_throughput', 125, help = 'AWS EFS throughput in MiB/s')


    def initialize_filesystem(self):
        ec2 = self.ec2(self.config['region'])
        efs = self.efs(self.config['region'])

        self.config['list'] = self.zones(self.ec2, self.config['region'])

        if not self.config['cidr']:
            response = ec2.describe_vpcs(
                VpcIds = [ self.config['vpc'] ]
            )
            # VPC CIDR (x.x.255.255 between 16 and 28)
            self.config['cidr'] = response['Vpcs'][0]['CidrBlock']
        
        # Subnet CIDR (between 16 and 28)
        subnets = self.get_subnets(self.config['cidr'], 28)

        if len(subnets) < len(self.config['list']):
            self.command.error("Length of available subnet CIDRs should be greater than {}".format(len(self.config['list'])))

        self.config['subnet_cidrs'] = {}
        for index, zone in enumerate(self.config['list']):
            self.config['subnet_cidrs'][zone] = str(subnets[index])

        self.config['creation_token'] = self._create_token()
        options = {
            'CreationToken': self.config['creation_token'],
            'PerformanceMode': self.config['performance_mode'],
            'ThroughputMode': self.config['throughput_mode']
        }
        if self.config['throughput_mode'] == 'provisioned':
            options['ProvisionedThroughputInMibps'] = self.config['provisioned_throughput']
        
        self.config['filesystem_id'] = self._init_filesystem(efs, options)
        self._get_filesystem(efs, self.config['filesystem_id'])

    def create_storage_mount(self, zone, storage):
        storage.region = storage.config['region']
        storage.zone = zone

        ec2 = self.ec2(storage.region)
        efs = self.efs(storage.region)

        subnet_cidr = storage.config['subnet_cidrs'][storage.zone]
        response = ec2.create_subnet(
            VpcId = storage.config['vpc'],
            AvailabilityZone = storage.zone,
            CidrBlock = subnet_cidr
        )
        storage.config['subnet_id'] = response['Subnet']['SubnetId']

        options = {
            'FileSystemId': storage.config['filesystem_id'],
            'SubnetId': storage.config['subnet_id']
        }
        if storage.config['sgroups']:
            sgroups = storage.config['sgroups']
            options['SecurityGroups'] = [sgroups] if isinstance(sgroups, str) else sgroups

        response = efs.create_mount_target(**options)

        storage.name = response['MountTargetId']
        storage.fs_name = storage.config['filesystem_id']
        storage.remote_host = response['IpAddress']
        storage.remote_path = '/'
        storage.mount_options = 'nfs4 nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2 0 0'


    def destroy_storage_mount(self):
        if not self.storage:
            self.command.error("Destroying storage requires a valid storage instance given to provider on initialization")
        
        ec2 = self.ec2(self.storage.region)
        efs = self.efs(self.storage.region)

        efs.delete_mount_target(
            MountTargetId = self.storage.name
        )
        ec2.delete_subnet(
            SubnetId = self.storage.config['subnet_id']
        )
       

    def _init_filesystem(self, efs, options):
        response = efs.create_file_system(**options)
        return response['FileSystemId']


    def _get_filesystem(self, efs, name, tries = 5, interval = 2):
        while True:
            try:
                result = efs.describe_file_systems(FileSystemId = name)
                filesystem = result['FileSystems'][0]
            
                if not filesystem['LifeCycleState'] in ('creating', 'updating', 'deleting'):
                    break
                
                time.sleep(interval)
            
            except Exception as e:
                if not tries:
                    self.command.error(e)
                
                time.sleep(interval)
                tries -= 1

        return filesystem


    def _create_token(self):
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.SystemRandom().choice(chars) for _ in range(32))
