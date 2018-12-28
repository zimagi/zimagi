from .base import DataMixin
from data.user import models


class UserMixin(DataMixin):

    def parse_user_name(self, optional = False):
        self._data_user = self._parse_variable(
            'user', str,
            'environment user name', 
            optional
        )

    @property
    def user_name(self):
        return self.options.get('user', None)

    @property
    def user(self):
        self._data_user = self._load_instance(
            self._user, self.user_name, 
            self._data_user
        )
        return self._data_user


    def parse_user_group(self, optional = False):
        self._data_user_group = self._parse_variable(
            'user_group', str,
            'environment user group', 
            optional
        )

    @property
    def user_group_name(self):
        return self.options.get('user_group', None)

    @property
    def user_group(self):
        self._data_user_group = self._load_instance(
            self._user_group, self.user_group_name, 
            self._data_user_group
        )
        return self._data_user_group


    def parse_user_groups(self, optional = False):
        self._data_user_groups = self._parse_variables(
            'user_groups', 'user_group', '--user-groups', str, 
            'environment user groups', 
            optional
        )

    @property
    def user_group_names(self):
        return self.options.get('user_groups', [])

    @property
    def user_groups(self):
        self._data_user_groups = self._load_instances(
            self._user_group, self.user_group_names, 
            self._data_user_groups
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
