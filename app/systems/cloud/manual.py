from django.conf import settings

from .base import BaseCloudProvider, CloudProviderError


class Manual(BaseCloudProvider):

    def server_config(self):
        self.requirement('region', help = 'Region name of server')
        self.requirement('name', help = 'Unique name of server in environment')
        self.requirement('ip', help = 'SSH capable IP of server')
        self.requirement('password', help = 'Password of server user')

        self.option('user', 'admin', help = 'Server SSH user')
        self.option('data_device', '/dev/sda4', help = 'Server data drive device')


    def create_server(self, server):
        if not self.check_ssh(
            server.ip, 
            server.user, 
            password = server.password
        ):
            raise CloudProviderError("Can not establish SSH connection to: {}".format(server))
