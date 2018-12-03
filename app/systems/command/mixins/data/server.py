
from systems.command import args
from data.server import models
from utility import text


class ServerMixin(object):

    def parse_server(self, optional = False):
        name = 'server'
        help_text = 'server name'

        self._data_server = None
        self.add_schema_field(name,
            args.parse_var(self.parser, name, str, help_text, optional),
            optional
        )

    @property
    def server_name(self):
        return self.options['server']

    @property
    def server(self):
        if not self._data_server:
            self._data_server = self._server.retrieve(self.server_name)

            if not self._data_server:
                self.error("Server {} does not exist".format(self.server_name))
        
        return self._data_server


    def parse_server_fields(self, optional = False):
        name = 'server_fields'

        excluded_fields = ('created', 'updated', 'environment')
        required = [x for x in self._server.required if x not in list(excluded_fields) + ['ssh_ip']]
        optional = [x for x in self._server.optional if x not in excluded_fields]
        help_text = "\n".join(text.wrap("server fields as key value pairs\n\ncreate required: {}\n\nupdate available: {}".format(", ".join(required), ", ".join(optional)), 60))

        self.add_schema_field(name,
            args.parse_key_values(self.parser, name, 'field=value', help_text, optional),
            optional
        )

    @property
    def server_fields(self):
        return self.options['server_fields']


    @property
    def _group(self):
        return models.Group.facade
    
    @property
    def _server(self):
        return models.Server.facade
