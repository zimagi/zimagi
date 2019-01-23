from django.core.management.base import CommandError

from . import DataMixin
from data.server import models

import re
import json


class ServerMixin(DataMixin):

    def parse_compute_provider_name(self, optional = False, help_text = 'compute resource provider'):
        self.parse_variable('compute_provider_name', optional, str, help_text)

    @property
    def compute_provider_name(self):
        return self.options.get('compute_provider_name', None)

    @property
    def compute_provider(self):
        return self.get_provider('compute', self.compute_provider_name)


    def parse_server_name(self, optional = False, help_text = 'unique environment server name'):
        self.parse_variable('server_name', optional, str, help_text)

    @property
    def server_name(self):
        return self.options.get('server_name', None)

    @property
    def server(self):
        return self.get_instance(self._server, self.server_name)

    def parse_server_fields(self, optional = False, help_callback = None):
        self.parse_fields(self._server, 'server_fields', optional, 
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


    def parse_server_group(self, optional = False, help_text = 'environment server group'):
        self.parse_variable('server_group', optional, str, help_text)

    @property
    def server_group_name(self):
        return self.options.get('server_group', None)

    @property
    def server_group(self):
        return self.get_instance(self._server_group, self.server_group_name)


    def parse_server_groups(self, flag = '--server-groups', help_text = 'one or more server group names'):
        self.parse_variables('server_groups', 'server_group', flag, str, help_text)

    @property
    def server_group_names(self):
        return self.options.get('server_groups', [])

    @property
    def server_groups(self):
        return self.get_instances(self._server_group, 
            names = self.server_group_names
        )


    def parse_server_reference(self, optional = False, help_text = 'unique environment server or group name'):
        self.parse_variable('server_reference', optional, str, help_text)

    @property
    def server_reference(self):
        return self.options.get('server_reference', 'all')

    @property
    def servers(self):
        return self.get_instances_by_reference(self._server, 
            self.server_reference,
            group_facade = self._server_group
        )


    @property
    def _server_group(self):
        return models.ServerGroup.facade
    
    @property
    def _server(self):
        return models.Server.facade

    
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
