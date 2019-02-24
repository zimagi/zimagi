from django.core.management.base import CommandError

from . import DataMixin
from data.federation.models import Federation


class FederationMixin(DataMixin):

    def parse_federation_provider_name(self, optional = False, help_text = 'federation resource provider'):
        self.parse_variable('federation_provider_name', optional, str, help_text, 'NAME')

    @property
    def federation_provider_name(self):
        return self.options.get('federation_provider_name', None)

    @property
    def federation_provider(self):
        provider = self.federation_provider_name
        if not provider and self.federation_name:
            provider = self.federation.type
        
        return self.get_provider('federation', provider)

    def parse_federation_name(self, optional = False, help_text = 'unique environment federation name'):
        self.parse_variable('federation_name', optional, str, help_text, 'NAME')

    @property
    def federation_name(self):
        return self.options.get('federation_name', None)

    @property
    def federation(self):
        return self.get_instance(self._federation, self.federation_name)
    
    def parse_federation_names(self, flag = '--federations', help_text = 'one or more federation names'):
        self.parse_variables('federation_names', flag, str, help_text, 'NAME')

    @property
    def federation_names(self):
        return self.options.get('federation_names', [])

    @property
    def federations(self):
        if self.federation_names:
            return self.get_instances(self._federation, 
                names = self.federation_names
            )
        return self.get_instances(self._federation)

    def parse_federation_fields(self, optional = False, help_callback = None):
        self.parse_fields(self._federation, 'federation_fields', optional, 
            (
                'created', 
                'updated', 
                'environment',
                'config'
            ),
            help_callback
        )

    @property
    def federation_fields(self):
        return self.options.get('federation_fields', {})


    @property
    def _federation(self):
        return self.facade(Federation.facade)
