from .base import DataMixin
from data.server import models


class ServerMixin(DataMixin):

    def parse_provider_name(self, optional = False):
        self._provider = self._parse_variable(
            'provider_name', str,
            'resource provider', 
            optional
        )

    @property
    def provider_name(self):
        return self.options.get('provider_name', None)

    @property
    def provider(self):
        if not self._provider:
            self._provider = self.cloud(self.provider_name)
        return self._provider


    def parse_server_name(self, optional = False):
        self._data_server = self._parse_variable(
            'server_name', str,
            'unique environment server name', 
            optional
        )

    @property
    def server_name(self):
        return self.options.get('server_name', None)

    @property
    def server(self):
        self._data_server = self._load_instance(
            self._server, self.server_name, 
            self._data_server
        )
        return self._data_server


    def parse_server_group(self, optional = False):
        self._data_server_group = self._parse_variable(
            'server_group', str,
            'environment server group', 
            optional
        )

    @property
    def server_group_name(self):
        return self.options.get('server_group', None)

    @property
    def server_group(self):
        self._data_server_group = self._load_instance(
            self._server_group, self.server_group_name, 
            self._data_server_group
        )
        return self._data_server_group


    def parse_server_groups(self, optional = False):
        self._data_server_groups = self._parse_variables(
            'server_groups', 'server_group', '--server-groups', str, 
            'one or more server group names', 
            optional
        )

    @property
    def server_group_names(self):
        return self.options.get('server_groups', [])

    @property
    def server_groups(self):
        self._data_server_groups = self._load_instances(
            self._server_group, self.server_group_names, 
            self._data_server_groups
        )
        return self._data_server_groups


    def parse_server_fields(self, optional = False, help_callback = None):
        self._parse_fields(self._server, 'server_fields', optional, 
            (
                'created', 
                'updated', 
                'environment'
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
