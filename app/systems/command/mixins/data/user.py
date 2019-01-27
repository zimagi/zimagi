from . import DataMixin
from data.user import models


class UserMixin(DataMixin):

    def parse_user_name(self, optional = False, help_text = 'environment user name'):
        self.parse_variable('user', optional, str, help_text, 'NAME')

    @property
    def user_name(self):
        return self.options.get('user', None)

    @property
    def user(self):
        return self.get_instance(self._user, self.user_name)


    def parse_user_group(self, optional = False, help_text = 'environment user group'):
        self.parse_variable('user_group', optional, str, help_text, 'NAME')

    @property
    def user_group_name(self):
        return self.options.get('user_group', None)

    @property
    def user_group(self):
        return self.get_instance(self._user_group, self.user_group_name)


    def parse_user_groups(self, flag = '--groups', help_text = 'environment user groups'):
        self.parse_variables('user_groups', flag, str, help_text, 'NAME')

    @property
    def user_group_names(self):
        return self.options.get('user_groups', [])

    @property
    def user_groups(self):
        return self.get_instances(self._user_group, 
            names = self.user_group_names
        )


    def parse_user_fields(self, optional = False):
        self.parse_fields(self._user, 'user_fields', optional, 
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
        return self.facade(models.User.facade)
   
    @property
    def _token(self):
        return self.facade(models.Token.facade)
   
    @property
    def _user_group(self):
        return self.facade(models.Group.facade)
