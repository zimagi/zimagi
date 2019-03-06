from data.server.models import Server
from . import NetworkMixin


class ServerMixin(NetworkMixin):

    schema = {
        'server': {
            'model': Server,
            'provider': True,                       
            'system_fields': (
                'environment',
                'subnet',
                'type',
                'config',
                'variables',
                'state_config',
                'created', 
                'updated'
            )
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.facade_index['03_server'] = self._server

  
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
