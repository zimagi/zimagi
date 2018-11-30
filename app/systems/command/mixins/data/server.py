
from systems.command import args
from data.server import models


class ServerMixin(object):

    def generate_schema(self):
        super().get_schema()
        self.schema['server'] = 'str'
        self.schema['server_fields'] = 'dict'


    def parse_server(self, optional = False):
        self._data_server = None
        args.parse_var(self.parser, 'server', str, 'server name', optional)

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
        args.parse_key_values(self.parser, 
            'server_fields',
            'field=value',
            'server fields as key value pairs', 
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
