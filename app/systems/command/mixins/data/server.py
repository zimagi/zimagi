
from data.server import models


class ServerMixin(object):

    def parse_server(self):
        self.parser.add_argument(
            'server', 
            nargs = 1, 
            type = str, 
            help = "server name"
        )

    @property
    def server(self):
        return self.options['server'][0]


    @property
    def _group(self):
        return models.Group.facade
    
    @property
    def _server(self):
        return models.Server.facade
