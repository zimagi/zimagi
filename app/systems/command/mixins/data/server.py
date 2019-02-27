from django.core.management.base import CommandError

from . import NetworkMixin
from data.server.models import Server
from utility import config

import re
import json


class ServerMixin(NetworkMixin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.facade_index['03_server'] = self._server


    def parse_server_provider_name(self, optional = False, help_text = 'server resource provider (default @server_provider|internal)'):
        self.parse_variable('server_provider_name', optional, str, help_text, 
            value_label = 'NAME'
        )

    @property
    def server_provider_name(self):
        name = self.options.get('server_provider_name', None)
        if not name:
            name = self.get_config('server_provider', required = False)
        if not name:
            name = config.Config.string('SERVER_PROVIDER', 'internal')
        return name

    @property
    def server_provider(self):
        return self.get_provider('compute', self.server_provider_name)


    def parse_server_name(self, optional = False, help_text = 'unique environment server name'):
        self.parse_variable('server_name', optional, str, help_text, 
            value_label = 'NAME'
        )

    @property
    def server_name(self):
        return self.options.get('server_name', None)

    def set_server_scope(self):
        if self.network_name:
            self._server.set_network_scope(self.network)
        else:
            network_name = self.get_config('network', required = False)
            if network_name:
                self._server.set_network_scope(self.get_instance(self._network, network_name))

    @property
    def server(self):
        return self.get_instance(self._server, self.server_name)

    def parse_server_fields(self, optional = False, help_callback = None):
        self.parse_fields(self._server, 'server_fields', 
            optional = optional, 
            excluded_fields = (
                'created', 
                'updated', 
                'environment',
                'config'
            ),
            help_callback = help_callback
        )

    @property
    def server_fields(self):
        return self.options.get('server_fields', {})


    def parse_server_reference(self, optional = False, help_text = 'unique environment server or group name'):
        self.parse_variable('server_reference', optional, str, help_text, 
            value_label = 'REFERENCE'
        )

    @property
    def server_reference(self):
        return self.options.get('server_reference', 'all')

    @property
    def servers(self):
        return self.get_servers_by_reference(self.server_reference)

   
    @property
    def _server(self):
        return self.facade(Server.facade)


    def get_servers_by_reference(self, reference = None, error_on_empty = True):
        
        def select_instances(type, facade, reference):
            results = []

            if reference:
                if ':' in reference:
                    components = reference.split(':')
                    network_name = components[0].strip()
                    reference = components[1].strip()
                    facade.set_network_scope(self.get_instance(self._network, network_name))
                
                elif (not type or type == 'network') and reference in list(self._network.keys()):
                    facade.set_network_scope(self.get_instance(self._network, reference))
                    results.extend(self.get_instances(facade))
                
                if (not type or type == 'subnet') and not results and reference in list(self._subnet.keys()):
                    results.extend(self.get_instances(facade, 
                        objects = list(facade.query(
                            subnet__name = reference
                        ))
                    ))

            return results
        
        return self.get_instances_by_reference(self._server, reference, 
            error_on_empty = error_on_empty,
            group_facade = self._group,
            selection_callback = select_instances
        )

    
    def ssh(self, server, timeout = 10, port = 22):
        if isinstance(server, str):
            server = self.get_instance(self._server, server)

        if not server:
            return None
        
        return super().ssh(
            "{}:{}".format(server.ip, port), server.user,
            password = server.password,
            key = server.private_key,
            timeout = timeout
        )
