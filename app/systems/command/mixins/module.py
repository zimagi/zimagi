from data.module.models import Module
from .base import DataMixin


class ModuleMixin(DataMixin):

    schema = {
        'module': {
            'model': Module,
            'provider': True,
            'default': 'git'
        },
        'profile': {}
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.facade_index['01_module'] = self._module


    def parse_profile_components(self, flag = '--components', help_text = 'one or more module profile component names'):
        self.parse_variables('profile_components', flag, str, help_text,
            value_label = 'NAME'
        )

    @property
    def profile_component_names(self):
        return self.options.get('profile_components', [])
