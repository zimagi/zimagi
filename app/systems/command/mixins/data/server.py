from django.core.management.base import CommandError

from .base import DataMixin
from data.server import models

import re
import json


class ServerMixin(DataMixin):

    STATE_RUNNING = 'running'
    STATE_UNREACHABLE = 'unreachable'


    def parse_compute_provider_name(self, optional = False, help_text = 'compute resource provider'):
        self._parse_variable('compute_provider_name', str, help_text, optional)

    @property
    def compute_provider_name(self):
        return self.options.get('compute_provider_name', None)

    @property
    def compute_provider(self):
        if not getattr(self, '_compute_provider', None):
            self._compute_provider = self.get_compute_provider(self.compute_provider_name)
        return self._compute_provider


    def parse_server_name(self, optional = False, help_text = 'unique environment server name'):
        self._parse_variable('server_name', str, help_text, optional)

    @property
    def server_name(self):
        return self.options.get('server_name', None)

    @property
    def server(self):
        self._data_server = self._load_instance(
            self._server, self.server_name, 
            getattr(self, '_data_server', None)
        )
        return self._data_server


    def parse_server_group(self, optional = False, help_text = 'environment server group'):
        self._parse_variable('server_group', str, help_text, optional)

    @property
    def server_group_name(self):
        return self.options.get('server_group', None)

    @property
    def server_group(self):
        self._data_server_group = self._load_instance(
            self._server_group, self.server_group_name, 
            getattr(self, '_data_server_group', None)
        )
        return self._data_server_group


    def parse_server_groups(self, optional = False, flag = '--server-groups', help_text = 'one or more server group names'):
        self._parse_variables('server_groups', 'server_group', flag, str, help_text, optional)

    @property
    def server_group_names(self):
        return self.options.get('server_groups', [])

    @property
    def server_groups(self):
        self._data_server_groups = self._load_instances(
            self._server_group, self.server_group_names, 
            getattr(self, '_data_server_groups', [])
        )
        return self._data_server_groups


    def parse_server_reference(self, optional = False, help_text = 'unique environment server or group name'):
        self._parse_variable('server_reference', str, help_text, optional)

    @property
    def server_reference(self):
        return self.options.get('server_reference', None)

    @property
    def servers(self):
        if not getattr(self, '_data_servers', None):
            self._data_servers = self.get_servers_by_reference(self.server_reference)
        return self._data_servers


    def parse_server_fields(self, optional = False, help_callback = None):
        self._parse_fields(self._server, 'server_fields', optional, 
            (
                'created', 
                'updated', 
                'environment',
                'config'
            ),
            help_callback
        )

    @property
    def server_fields(self):
        return self.options.get('server_fields', {})


    @property
    def _server_group(self):
        return models.ServerGroup.facade
    
    @property
    def _server(self):
        return models.Server.facade


    def get_servers_by_reference(self, reference = None, error_on_empty = True):
        server_results = []
        if reference and reference != 'all':
            matches = re.search(r'^([^\=]+)\s*\=\s*(.+)', reference)

            if matches:
                field = matches.group(1)
                value = matches.group(2)

                if field != 'state':
                    servers = self._server.query(**{ field: value })
                    states = None
                else:
                    servers = self._server.all()
                    states = [value]
                    
                if len(servers) > 0:
                    server_results.extend(self.get_servers(
                        instances = list(servers), 
                        states = states
                    ))
            else:
                server = self._server.retrieve(reference)
                if server:
                    server_results.extend(self.get_servers(instances = server))
                else:
                    group = self._server_group.retrieve(reference)
                    if group:
                        server_results.extend(self.get_servers(groups = reference))
        else:
            server_results.extend(self.get_servers())
        
        if error_on_empty and not server_results:
            if reference:
                self.error("No servers were found: {}".format(reference))
            else:
                self.error("No servers were found")
        
        return server_results

    def get_servers(self, names = [], groups = [], instances = [], states = None):
        server_items = []
        servers = []

        if not getattr(self, '_data_server_cache', None):
            self._data_server_cache = {}

        if isinstance(names, str):
            names = [names]
        
        if names:
            server_items.extend(names)

        if isinstance(groups, str):
            groups = [groups]
        
        for group in groups:
            server_items.extend(self._server.field_values('name', groups__name = group))        

        if not isinstance(instances, (list, tuple)):
            instances = [instances]

        if instances:
            server_items.extend(instances)

        if states and not isinstance(states, (list, tuple)):
            states = [states]

        if not server_items and not names and not groups and not instances and not states:
            server_items = self._server.all()            

        def init_server(server, state):
            if isinstance(server, str):
                server = self._server.retrieve(server)
            if server:
                if not server.name in self._data_server_cache:
                    if isinstance(server.config, str):
                        server.config = json.loads(server.config)
                    
                    server.compute_provider = self.get_compute_provider(server.type, server = server)
                    server.state = self.__class__.STATE_RUNNING if self.ping(server) else self.__class__.STATE_UNREACHABLE
                    self._data_server_cache[server.name] = server
                else:
                    server = self._data_server_cache[server.name]

                if not states or server.state in states:
                    servers.append(server)
            else:
                self.error("Server {} does not exist".format(name))

        self.run_list(server_items, init_server)
        return servers


    def running(self, server):
        if server.state == self.__class__.STATE_RUNNING:
            return True
        return False

    
    def ssh(self, server, timeout = 10, port = 22):
        if isinstance(server, str):
            server = self.get_servers(names = server)
        
        return super().ssh(
            "{}:{}".format(server.ip, port), server.user,
            password = server.password,
            key = server.private_key,
            timeout = timeout
        )

    def ping(self, server, port = 22):
        if isinstance(server, str):
            server = self.get_servers(names = server)
        
        return server.compute_provider.ping(port = port)
