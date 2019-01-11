from .base import DataMixin
from data.user import models


class UserMixin(DataMixin):

    def parse_user_name(self, optional = False, help_text = 'environment user name'):
        self._parse_variable('user', optional, str, help_text)

    @property
    def user_name(self):
        return self.options.get('user', None)

    @property
    def user(self):
        self._data_user = self._load_instance(
            self._user, self.user_name, 
            getattr(self, '_data_user', None)
        )
        return self._data_user


    def parse_user_group(self, optional = False, help_text = 'environment user group'):
        self._parse_variable('user_group', optional, str, help_text)

    @property
    def user_group_name(self):
        return self.options.get('user_group', None)

    @property
    def user_group(self):
        self._data_user_group = self._load_instance(
            self._user_group, self.user_group_name, 
            getattr(self, '_data_user_group', None)
        )
        return self._data_user_group


    def parse_user_groups(self, flag = '--user-groups', help_text = 'environment user groups'):
        self._parse_variables('user_groups', 'user_group', flag, str, help_text)

    @property
    def user_group_names(self):
        return self.options.get('user_groups', [])

    @property
    def user_groups(self):
        self._data_user_groups = self._load_instances(
            self._user_group, self.user_group_names, 
            getattr(self, '_data_user_groups', [])
        )
        return self._data_user_groups


    def parse_user_fields(self, optional = False):
        self._parse_fields(self._user, 'user_fields', optional, 
            (
                'password', 
                'date_joined', 
                'last_login', 
                'is_superuser', 
                'is_staff', 
                'is_active'
            )
        )

    @property
    def user_fields(self):
        return self.options.get('user_fields', {})

   
    @property
    def _user(self):
        return models.User.facade
   
    @property
    def _token(self):
        return models.Token.facade
   
    @property
    def _user_group(self):
        return models.Group.facade
