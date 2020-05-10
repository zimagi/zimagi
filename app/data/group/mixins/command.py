from data.group.models import Group
from .base import DataMixin


class GroupMixin(DataMixin):

    schema = {
        'group': {
            'model': Group,
            'provider': True
        },
        'parent': {
            'model': Group
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.facade_index['02_group'] = self._group
