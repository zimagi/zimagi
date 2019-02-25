from . import DataMixin
from data.user.models import User
from utility import config


class UserMixin(DataMixin):

    def __init__(self, stdout = None, stderr = None, no_color = False):
        super().__init__(stdout, stderr, no_color)
        self.facade_index['00_user'] = self._user


    def parse_user_provider_name(self, optional = False, help_text = 'system user provider (default @user_provider|internal)'):
        self.parse_variable('user_provider_name', optional, str, help_text, 'NAME')

    @property
    def user_provider_name(self):
        name = self.options.get('user_provider_name', None)
        if not name:
            name = self.get_config('user_provider', required = False)
        if not name:
            name = config.Config.string('USER_PROVIDER', 'internal')
        return name

    @property
    def user_provider(self):
        return self.get_provider('user', self.user_provider_name)


    def parse_user_name(self, optional = False, help_text = 'environment user name'):
        self.parse_variable('user', optional, str, help_text, 'NAME')

    @property
    def user_name(self):
        return self.options.get('user', None)

    @property
    def user(self):
        return self.get_instance(self._user, self.user_name)

    def parse_user_fields(self, optional = False, help_callback = None):
        self.parse_fields(self._user, 'user_fields', optional, [],
            help_callback
        )

    @property
    def user_fields(self):
        return self.options.get('user_fields', {})

   
    @property
    def _user(self):
        return self.facade(User.facade)
