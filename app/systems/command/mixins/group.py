from data.group.models import Group
from .base import DataMixin


class GroupMixin(DataMixin):

    schema = {
        'group': {
            'model': Group,
            'provider': True,
            'system_fields': (
                'environment',
                'parent',
                'type',
                'config',
                'variables',
                'state_config',
                'created',
                'updated'
            )
        },
        'parent': {
            'model': Group
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.facade_index['01_group'] = self._group
