from django.conf import settings

from . import DataMixin
from data.group.models import Group
from utility import config


class GroupMixin(DataMixin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.facade_index['01_group'] = self._group


    def parse_group_provider_name(self, optional = False, help_text = 'environment group provider (default @group_provider|internal)'):
        self.parse_variable('group_provider_name', optional, str, help_text, 
            value_label = 'NAME'
        )

    @property
    def group_provider_name(self):
        name = self.options.get('group_provider_name', None)
        if not name:
            name = self.get_config('group_provider', required = False)
        if not name:
            name = config.Config.string('GROUP_PROVIDER', 'internal')
        return name

    @property
    def group_provider(self):
        return self.get_provider('group', self.group_provider_name)


    def parse_group_name(self, optional = False, help_text = 'environment group'):
        self.parse_variable('group_name', optional, str, help_text, 
            value_label = 'NAME'
        )

    @property
    def group_name(self):
        return self.options.get('group_name', None)

    def parse_group_parent_name(self, optional = False, help_text = 'environment group parent'):
        self.parse_variable('group_parent_name', optional, str, help_text, 
            value_label = 'NAME'
        )

    @property
    def group_parent_name(self):
        return self.options.get('group_parent_name', None)

    @property
    def group(self):
        return self.get_instance(self._group, self.group_name)

    def parse_group_fields(self, optional = False, help_callback = None):
        self.parse_fields(self._group, 'group_fields', 
            optional = optional, 
            excluded_fields = (
                'created',
                'updated',
                'environment',
                'parent',
                'type',
                'config',
                'variables',
                'state_config'
            ),
            help_callback = help_callback
        )

    @property
    def group_fields(self):
        return self.options.get('group_fields', {})


    def parse_group_names(self, flag = '--groups', help_text = 'one or more group names'):
        self.parse_variables('group_names', flag, str, help_text, 
            value_label = 'NAME'
        )

    @property
    def group_names(self):
        return self.options.get('group_names', [])

    @property
    def groups(self):
        if self.group_names:
            return self.get_instances(self._group, 
                names = self.group_names
            )
        return self.get_instances(self._group)


    def parse_group_order(self, optional = '--order', help_text = 'group ordering fields (~field for desc)'):
        self.parse_variables('group_order', optional, str, help_text, 
            value_label = '[~]FIELD'
        )

    @property
    def group_order(self):
        return self.options.get('group_order', [])


    def parse_group_search(self, optional = True, help_text = 'group search fields'):
        self.parse_variables('group_search', optional, str, help_text, 
            value_label = 'REFERENCE'
        )

    @property
    def group_search(self):
        return self.options.get('group_search', [])

    @property
    def group_instances(self):
        return self.search_instances(self._group, self.group_search)


    @property
    def _group(self):
        return self.facade(Group.facade)
