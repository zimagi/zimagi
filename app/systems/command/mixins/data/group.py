from data.group.models import Group
from . import DataMixin


class GroupMixin(DataMixin):

    schema = {
        'group': {
            'model': Group,
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
        self.facade_index['01_group'] = self._group


    def parse_group_parent_name(self, optional = False, help_text = 'environment group parent'):
        self.parse_variable('group_parent_name', optional, str, help_text, 
            value_label = 'NAME'
        )

    @property
    def group_parent_name(self):
        return self.options.get('group_parent_name', None)
