from data.module.models import Module
from .base import DataMixin


class ModuleMixin(DataMixin):

    schema = {
        'module': {
            'model': Module,
            'provider': True,
            'default': 'git'
        },
        'profile': {},
        'task': {}
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.facade_index['01_module'] = self._module


    def parse_display_only(self):
        self.parse_flag('display_only', '--display_only', 'render combined module profile without executing')

    @property
    def display_only(self):
        return self.options.get('display_only', False)


    def parse_profile_components(self, flag = '--components', help_text = 'one or more module profile component names'):
        self.parse_variables('profile_components', flag, str, help_text,
            value_label = 'NAME'
        )

    @property
    def profile_component_names(self):
        return self.options.get('profile_components', [])
