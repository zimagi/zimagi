from io import StringIO

from django.conf import settings

from systems.command import providers
from utility import ssh as sshlib

import threading
import time
import copy


class ServerResult(object):

    def __init__(self, type, config, groups,
        name = None,
        region = None,
        zone = None,
        ip = None, 
        user = None, 
        password = None, 
        private_key = None,
        data_device = None
    ):
        self.type = type
        self.config = copy.deepcopy(config)
        self.groups = [groups] if isinstance(groups, str) else groups
        self.name = name
        self.region = region
        self.zone = zone
        self.ip = ip
        self.user = user
        self.password = password
        self.private_key = private_key
        self.data_device = data_device

    def __str__(self):
        return "[{}:{}:{}]> {} ({}@{})".format(
            self.type,
            self.region,
            self.zone,
            self.name,
            self.user,
            self.ip          
        )


class BaseComputeProvider(providers.BaseCommandProvider):

    def __init__(self, name, command, server = None):
        super().__init__(name, command)

        self.server = server
        self.thread_lock = threading.Lock()

        self.provider_type = 'compute'
        self.provider_options = settings.COMPUTE_PROVIDERS


    def create_servers(self, config, groups = [], complete_callback = None):
        self.config = config
        
        self.provider_config()
        self.validate()

        def server_callback(index):
            server = ServerResult(self.name, config, [self.name] + groups)

            for key, value in self.config.items():
                if hasattr(server, key) and key not in ('type', 'config', 'groups'):
                    setattr(server, key, value)

            return server
        
        self.initialize_servers()

        return self.command.run_list(
            self.config.pop('list', [0]), 
            self.create_server,
            state_callback = server_callback,
            complete_callback = complete_callback
        )

    def initialize_servers(self):
        # Override in subclass
        pass

    def create_server(self, index, server):
        # Override in subclass
        pass

    def destroy_server(self):
        # Override in subclass
        pass

    def rotate_key(self):
        if not self.server:
            self.command.error("Rotating server key requires a valid server instance given to provider on initialization")
        
        (private_key, public_key) = sshlib.SSH.create_keypair()

        self.ssh().exec('echo "{}" > "$HOME/.ssh/authorized_keys"'.format(public_key))
        self.server.private_key = private_key

    def rotate_password(self):
        if not self.server:
            self.command.error("Rotating server password requires a valid server instance given to provider on initialization")
        
        password = sshlib.SSH.create_password()

        self.command.project.provider.exec(
            'password',
            self.server,
            {
                "user": self.server.user, 
                "password": password
            }
        )
        self.server.password = password


    def ssh(self, timeout = 10, port = 22):
        if not self.server:
            self.command.error("SSH requires a valid server instance given to provider on initialization")

        return self.command.ssh(self.server, timeout = timeout, port = port)

    def check_ssh(self, port = 22, tries = 10, interval = 2, timeout = 10, silent = False, server = None):
        if not self.server and not server:
            self.command.error("Checking SSH requires a valid server instance given to provider on initialization")
        if not server:
            server = self.server

        host = "{}:{}".format(server.ip, port)

        while True:
            if not tries:
                break
            try:
                if not silent:
                    self.command.info("Checking {}@{} SSH connection".format(server.user, host))
                
                sshlib.SSH(host, server.user, server.password, 
                    key = server.private_key, 
                    timeout = timeout
                )
                return True
            
            except Exception as e:
                time.sleep(interval)
                tries -= 1
        
        return False

    def ping(self, port = 22):
        if not self.server:
            self.command.error("Ping requires a valid server instance given to provider on initialization")
        
        return self.check_ssh(
            port = port,
            tries = 1,
            timeout = 1,
            silent = True
        )
