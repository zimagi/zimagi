
from systems.command import args
from data.user import models


class UserMixin(object):

    def parse_user(self):
        self._data_user = None
        args.parse_var(self.parser, 'user', str, 'environment user name')

    @property
    def user_name(self):
        return self.options['user']

    @property
    def user(self):
        if not self._data_user:
            self._data_user = self._user.retrieve(self.user_name)

            if not self._data_user:
                self.error("User {} does not exist".format(self.user_name))
        
        return self._data_user

   
    @property
    def _user(self):
        return models.User.facade
