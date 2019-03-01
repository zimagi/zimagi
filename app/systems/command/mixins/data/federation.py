from data.federation.models import Federation
from . import DataMixin


class FederationMixin(DataMixin):

    schema = {
        'federation': {
            'model': Federation,
            'provider': True,                       
            'system_fields': (
                'environment',
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
        self.facade_index['02_federation'] = self._federation
