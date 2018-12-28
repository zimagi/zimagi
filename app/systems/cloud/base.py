from utility import ssh

import threading
import time
import traceback


class CloudProviderError(Exception):
    pass


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

    def __init__(self, command):
        self.name = type(self).__name__
        self.command = command
        self.errors = []
        self.config = {}
        self.schema = ParamSchema()

        self.thread_lock = threading.Lock()


    def server_config(self):
        # Override in subclass
        pass

    def server_schema(self):
        self.schema.clear()
        self.server_config()
        return self.schema.export()


    def create_servers(self, config, groups = [], complete_callback = None):
        self.errors = []
        self.config = config
        results = []
        threads = []
        errors = []

        self.server_config()
        self.validate()

        for index in range(0, self.config.get('count', 1)):
            server = ServerResult(self.name, config, groups)

            for key, value in self.config.items():
                if hasattr(server, key) and key not in ('type', 'config', 'groups'):
                    setattr(server, key, value)

            thread = threading.Thread(target = self.thread_wrapper, args = (index, errors, complete_callback, self.create_server, server))
            thread.start()

            threads.append(thread)
            results.append(server)

        for thread in threads:
            thread.join()

        if errors:
            message = "\n".join(errors)
            raise CloudProviderError(message)

        return results

    def create_server(self, server):
        # Override in subclass
        pass

    def halt_servers(self, names):
        names = [names] if isinstance(names, str) else names
        return True

    def destroy_servers(self, names):
        return True


    def validate(self):
        if self.errors:
            messages = "\n".join(self.errors)
            raise CloudProviderError(messages)
    
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


    def check_ssh(self, hostname, username, password = None, key = None, port = 22, tries = 30, interval = 2):
        host = "{}:{}".format(hostname, port)

        while True:
            try:
                ssh.SSH(host, username, password, key)
                return True
            
            except Exception as e:
                if not tries:
                    break
                time.sleep(interval)
                tries -= 1
        
        return False


    def thread_wrapper(self, index, errors, complete_callback, callback, *args, **options):
        try:
            callback(*args, **options)

            if complete_callback and callable(complete_callback):
                with self.thread_lock:
                    complete_callback(*args, **options)
        
        except Exception as e:
            errors.append("[Thread {}] - {}".format(index, e))
