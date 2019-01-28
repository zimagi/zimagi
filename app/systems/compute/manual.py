from .base import BaseComputeProvider


class Manual(BaseComputeProvider):

    def provider_config(self, type = None):
        self.requirement('name', help = 'Unique name of server in environment')
        self.requirement('ip', help = 'SSH capable IP of server')
        self.requirement('password', help = 'Password of server user')

        self.option('user', 'admin', help = 'Server SSH user', config_name = 'manual_user')
        self.option('data_device', '/dev/sda4', help = 'Server data drive device', config_name = 'manual_data_device')


    def create_provider_server(self, index, server):
        if server.subnet.network.type != 'man':
            self.command.error("Manually defined network needed to create manual server entries")

        if not self.check_ssh(server = server):
            self.command.error("Can not establish SSH connection to: {}".format(server))
