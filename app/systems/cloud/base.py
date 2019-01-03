from io import StringIO

from django.core.management.base import CommandError

from utility import ssh as sshlib

import threading
import time
import paramiko


class ServerResult(object):

    def __init__(self, type, config, groups, 
        region = None, 
        name = None, 
        ip = None, 
        user = None, 
        password = None, 
        private_key = None,
        data_device = None
    ):
        self.type = type
        self.config = config
        self.groups = [groups] if isinstance(groups, str) else groups
        self.region = region
        self.name = name
        self.ip = ip
        self.user = user
        self.password = password
        self.private_key = private_key
        self.data_device = data_device

    def __str__(self):
        return "[{}:{}]> {} ({}@{})".format(
            self.type,
            self.region,
            self.name,
            self.user,
            self.ip          
        )


class ParamSchema(object):

    def __init__(self):
        self.clear()

    def clear(self):
        self.schema = {
            'requirements': [],
            'options': []
        }

    def require(self, name, help):
        if name in self.schema['options']:
            return
        if name not in self.schema['requirements']:
            self.schema['requirements'].append({
                'name': name,
                'help': help
            })

    def option(self, name, default, help):
        self.schema['options'].append({
            'name': name,
            'default': default,
            'help': help
        })

    def export(self):
        return self.schema


class BaseCloudProvider(object):

    def __init__(self, name, command, server = None):
        self.name = name
        self.command = command
        self.errors = []
        self.config = {}
        self.schema = ParamSchema()
        self.server = server

        self.thread_lock = threading.Lock()


    def server_config(self):
        # Override in subclass
        pass

    def server_schema(self):
        self.schema.clear()
        self.server_config()
        return self.schema.export()


    def create_servers(self, config, groups = [], complete_callback = None):
        self.config = config
        
        self.server_config()
        self.validate()

        def server_callback(index):
            server = ServerResult(self.name, config, [self.name] + groups)

            for key, value in self.config.items():
                if hasattr(server, key) and key not in ('type', 'config', 'groups'):
                    setattr(server, key, value)

            return server

        results = self.command.run_list(
            range(0, int(self.config.pop('count', 1))), 
            self.create_server,
            state_callback = server_callback,
            complete_callback = complete_callback
        )            
        if results.aborted:
            for thread in results.errors:
                if not isinstance(thread.error, CommandError):
                    self.command.error("[{}] - {}".format(thread.name, thread.error), terminate = False)
            
            self.command.error("Server creation failed")

        return results

    def create_server(self, index, server):
        # Override in subclass
        pass

    def destroy_server(self):
        # Override in subclass
        pass

    def rotate_key(self):
        if not self.server:
            self.command.error("Rotating server key requires a valid server instance given to provider on initialization")
        
        (private_key, public_key) = self.create_keypair()

        self.ssh().exec('echo "{}" > "$HOME/.ssh/authorized_keys"'.format(public_key))
        self.server.private_key = private_key


    def validate(self):
        if self.errors:
            self.command.error("\n".join(self.errors))
    
    def option(self, name, default = None, callback = None, help = None):
        self.schema.option(name, default, help)

        if not self.config.get(name, None):
            self.config[name] = default
        
        elif callback and callable(callback):
            callback(name, self.config[name], self.errors)        

    def requirement(self, name, callback = None, help = None):
        self.schema.require(name, help)

        if not self.config.get(name, None):
            self.errors.append("Field '{}' required when adding {} servers".format(name, self.name))
        
        elif callback and callable(callback):
            callback(name, self.config[name], self.errors)


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


    def create_keypair(self):
        key = paramiko.RSAKey.generate(4096)
        private_str = StringIO()
        key.write_private_key(private_str)
        return (private_str.getvalue(), "ssh-rsa {}".format(key.get_base64()))
