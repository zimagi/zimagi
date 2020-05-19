from data.module.models import Module
from .base import BaseMixin


class ModuleMixin(BaseMixin):

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
        self.parse_flag('display_only', '--display-only', 'render combined module profile without executing')

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


    def parse_profile_config_fields(self, optional = True, help_callback = None):
        self.parse_fields(None, 'profile_config_fields',
            optional = optional,
            help_callback = help_callback
        )

    @property
    def profile_config_fields(self):
        return self.options.get('profile_config_fields', {})


    def parse_ignore_missing(self):
        self.parse_flag('ignore_missing', '--ignore-missing', 'ignore missing profile instead of throwing an error')

    @property
    def ignore_missing(self):
        return self.options.get('ignore_missing', False)
