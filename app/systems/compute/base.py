from io import StringIO

from django.conf import settings

from systems.command import providers
from utility import ssh as sshlib

import threading
import time
import copy


class ServerResult(object):

    def __init__(self, type, subnet, firewalls, config, groups,
        name = None,
        ip = None, 
        user = None, 
        password = None, 
        private_key = None,
        data_device = None,
        backup_device = None
    ):
        self.type = type
        self.subnet = subnet
        self.firewalls = firewalls
        self.config = copy.deepcopy(config)
        self.groups = [groups] if isinstance(groups, str) else groups
        self.name = name
        self.ip = ip
        self.user = user
        self.password = password
        self.private_key = private_key
        self.data_device = data_device
        self.backup_device = backup_device

    def __str__(self):
        return "[{}:{}]> {} ({}@{})".format(
            self.type,
            self.subnet.name,
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


    def create_server_name(self):
        state_variable = 'server_name_index'

        name_index = self.command.get_state(state_variable)
        name_index = int(name_index) + 1 if name_index else 1
        
        self.command.set_state(state_variable, name_index)
        return "cs{}".format(name_index)


    def create_servers(self, subnet, config, groups = [], firewalls = [], complete_callback = None):
        self.config = config
        
        self.provider_config()
        self.validate()

        def server_callback(index):
            server = ServerResult(self.name, subnet, firewalls, config, [self.name] + groups)
            
            for key, value in self.config.items():
                if hasattr(server, key) and key not in ('type', 'config', 'groups', 'firewalls'):
                    setattr(server, key, value)

            return server
        
        self.initialize_provider_servers()

        return self.command.run_list(
            self.config.pop('list', [0]), 
            self.create_provider_server,
            state_callback = server_callback,
            complete_callback = complete_callback
        )

    def initialize_provider_servers(self):
        # Override in subclass
        pass

    def create_provider_server(self, index, server):
        # Override in subclass
        pass

    def destroy_server(self, abort = False):
        if not self.server:
            self.command.error("Destroying server requires a valid server instance given to provider on initialization")
        try:
            self.destroy_provider_server()
        
        except Exception as e:
            if abort:
                raise e
            else:
                self.command.warning(str(e))

    def destroy_provider_server(self):
        # Override in subclass
        pass


    def rotate_key(self):
        if not self.server:
            self.command.error("Rotating server key requires a valid server instance given to provider on initialization")
        
        (private_key, public_key) = sshlib.SSH.create_keypair()

        ssh = self.ssh()
        ssh.exec('mkdir -p "$HOME/.ssh"')
        ssh.exec('chmod 700 "$HOME/.ssh"')
        ssh.exec('echo "{}" > "$HOME/.ssh/authorized_keys"'.format(public_key))
        ssh.exec('chmod 600 "$HOME/.ssh/authorized_keys"')
        
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
