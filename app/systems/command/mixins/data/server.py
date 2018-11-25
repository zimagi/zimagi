
from systems.command import args
from data.server import models


class ServerMixin(object):

    def parse_server(self):
        args.parse_var(self.parser, 'server', str, 'server name')

    @property
    def server(self):
        return self.options['server']


    def parse_server_fields(self):
        args.parse_key_values(self.parser, 
            'server_fields',
            'field=value',
            'server fields as key value pairs'
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
