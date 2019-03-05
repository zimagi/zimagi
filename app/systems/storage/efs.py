from utility.cloud import AWSServiceMixin
from .base import *


class EFSStorageProvider(AWSServiceMixin, StorageProvider):

    def provider_config(self, type = None):
        self.option(str, 'performance_mode', 'generalPurpose', help = 'AWS EFS performance mode (can also be: maxIO)', config_name = 'aws_efs_perf_mode')
        self.option(str, 'throughput_mode', 'bursting', help = 'AWS EFS throughput mode (can also be: provisioned)', config_name = 'aws_efs_tp_mode')
        self.option(int, 'provisioned_throughput', None, help = 'AWS EFS throughput in MiB/s', config_name = 'aws_efs_prov_tp')
        self.option(bool, 'encrypted', False, help = 'AWS EFS encrypted filesystem?', config_name = 'aws_efs_encrypted')

    def initialize_terraform(self, instance, created):
        if instance.network.type != 'aws':
            self.command.error("AWS VPC network needed to create AWS EFS storage filesystems")

        self.aws_credentials(instance.config)
        super().initialize_terraform(instance, created)

    def finalize_terraform(self, instance):
        self.aws_credentials(instance.config)
        super().finalize_terraform(instance)

    def prepare_instance(self, instance, created):
        super().prepare_instance(instance, created)
        self.clean_aws_credentials(instance.config)


class EFSStorageMountProvider(AWSServiceMixin, StorageMountProvider):

    def initialize_terraform(self, instance, created):
        relations = instance.facade.get_relation_names(self.command)

        super().initialize_terraform(instance, created)
        self.aws_credentials(instance.config)
        
        instance.config['security_groups'] = self.get_security_groups(relations.get('firewalls', []))

    def prepare_instance(self, instance, created):
        instance.remote_path = '/'
        instance.remote_host = instance.variables['mount_ip']
        super().prepare_instance(instance, created)
        self.clean_aws_credentials(instance.config)    

    def finalize_terraform(self, instance):
        self.aws_credentials(instance.config)
        super().finalize_terraform(instance)


class AWSEFS(BaseStorageProvider):
    
    def register_types(self):
        super().register_types()
        self.set('storage', EFSStorageProvider)
        self.set('mount', EFSStorageMountProvider)
