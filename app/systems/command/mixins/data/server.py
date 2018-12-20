from django.conf import settings

from systems.command import args
from data.server import models
from utility import text


class ServerMixin(object):

    def parse_provider_name(self, optional = False):
        name = 'provider_name'
        help_text = 'resource provider'

        self._provider = None
        self.add_schema_field(name,
            args.parse_var(self.parser, name, str, help_text, optional),
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
        name = 'server_name'
        help_text = 'unique environment server name'

        self._data_server = None
        self.add_schema_field(name,
            args.parse_var(self.parser, name, str, help_text, optional),
            optional
        )

    @property
    def server_name(self):
        return self.options.get('server_name', None)

    @property
    def server(self):
        if not self._data_server:
            self._data_server = self._server.retrieve(self.server_name)

            if not self._data_server:
                self.error("Server {} does not exist".format(self.server_name))
        
        return self._data_server


    def parse_server_fields(self, optional = False, help_callback = None):
        name = 'server_fields'

        if help_callback and callable(help_callback):
            help_text = "\n".join(help_callback())
        else:
            excluded_fields = ('created', 'updated', 'environment')
            required = [x for x in self._server.required if x not in list(excluded_fields)]
            optional = [x for x in self._server.optional if x not in excluded_fields]
            help_text = "\n".join(text.wrap("provider fields as key value pairs\n\nrequirements: {}\n\noptions: {}".format(", ".join(required), ", ".join(optional)), 60))

        self.add_schema_field(name,
            args.parse_key_values(self.parser, name, 'field=value', help_text, optional),
            optional
        )

    @property
    def server_fields(self):
        return self.options.get('server_fields', {})


    def parse_server_groups(self):
        name = 'server_groups'
        help_text = 'one or more server group names (comma separated)'

        self.add_schema_field(name,
            args.parse_csv_option(self.parser, name, '--groups', help_text, None),
            True
        )

    @property
    def server_groups(self):
        return self.options.get('server_groups', [])


    @property
    def _server_group(self):
        return models.ServerGroup.facade
    
    @property
    def _server(self):
        return models.Server.facade
