from data.project.models import Project
from .base import DataMixin


class ProjectMixin(DataMixin):

    schema = {
        'project': {
            'model': Project,
            'provider': True,
            'default': 'git',
            'system_fields': (
                'environment',
                'type',
                'config',
                'variables',
                'state_config',
                'created',
                'updated'
            )
        },
        'profile': {},
        'task': {}
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.facade_index['01_project'] = self._project


    def parse_profile_components(self, flag = '--components', help_text = 'one or more project profile component names'):
        self.parse_variables('profile_components', flag, str, help_text,
            value_label = 'NAME'
        )

    @property
    def profile_component_names(self):
        return self.options.get('profile_components', [])
