from . import DataMixin
from data.user.models import User


class UserMixin(DataMixin):

    def parse_user_name(self, optional = False, help_text = 'environment user name'):
        self.parse_variable('user', optional, str, help_text, 'NAME')

    @property
    def user_name(self):
        return self.options.get('user', None)

    @property
    def user(self):
        return self.get_instance(self._user, self.user_name)

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
        return self.facade(User.facade)
