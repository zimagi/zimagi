from utility import cloud
from .base import BaseStorageProvider
from utility import data

import time
import json


class AWSEFS(cloud.AWSServiceMixin, BaseStorageProvider):

    def provider_config(self, type = None):
        if type == 'storage':
            self.option(str, 'performance_mode', 'generalPurpose', help = 'AWS EFS performance mode (can also be: maxIO)', config_name = 'aws_efs_perf_mode')
            self.option(str, 'throughput_mode', 'bursting', help = 'AWS EFS throughput mode (can also be: provisioned)', config_name = 'aws_efs_tp_mode')
            self.option(int, 'provisioned_throughput', 125, help = 'AWS EFS throughput in MiB/s', config_name = 'aws_efs_prov_tp')
        
        elif type == 'mount':
            pass


    def create_provider_storage(self, storage):
        if storage.network.type != 'aws_vpc':
            self.command.error("AWS VPC network needed to create AWS EFS storage filesystems")

        efs = self.efs(storage.network.config['region'])

        storage.config['creation_token'] = data.create_token()
        options = {
            'CreationToken': storage.config['creation_token'],
            'PerformanceMode': storage.config['performance_mode'],
            'ThroughputMode': storage.config['throughput_mode']
        }
        if storage.config['throughput_mode'] == 'provisioned':
            options['ProvisionedThroughputInMibps'] = storage.config['provisioned_throughput']
        
        response = efs.create_file_system(**options)
        storage.config['filesystem_id'] = response['FileSystemId']


    def destroy_provider_storage(self):
        efs = self.efs(self.storage.network.config['region'])
        efs.delete_file_system(
            FileSystemId = self.storage.config['filesystem_id']
        )


    def create_provider_mount(self, mount):
        efs = self.efs(self.storage.network.config['region'])

        options = {
            'FileSystemId': self.storage.config['filesystem_id'],
            'SubnetId': mount.subnet.config['subnet_id']
        }
        if mount.firewalls:
            sgroups = self.get_security_groups(mount.firewalls)
            options['SecurityGroups'] = sgroups

        response = efs.create_mount_target(**options)
        mount.config['target_id'] = response['MountTargetId']
        
        mount.remote_host = response['IpAddress']
        mount.remote_path = '/'
        mount.mount_options = 'nfs4 nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2 0 0'


    def update_provider_mount_firewalls(self, mount, firewalls):
        efs = self.efs(self.storage.network.config['region'])
        efs.modify_mount_target_security_groups(
            MountTargetId = mount.config['target_id'],
            SecurityGroups = self.get_security_groups(firewalls)
        )


    def destroy_provider_mount(self, mount):
        efs = self.efs(self.storage.network.config['region'])
        efs.delete_mount_target(
            MountTargetId = mount.config['target_id']
        )
