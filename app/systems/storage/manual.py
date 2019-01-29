from .base import BaseStorageProvider


class Manual(BaseStorageProvider):

    def provider_config(self, type = None):
        if type == 'storage':
            pass

        elif type == 'mount':
            self.requirement('remote_host', help = 'Remote host to connect storage mount')
        
            self.option('remote_path', '/', help = 'Remote path to mount locally', config_name = 'manual_remote_path')
            self.option('mount_options', 'nfs4 rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2 0 0', help = 'Mount options', config_name = 'manual_mount_options')
