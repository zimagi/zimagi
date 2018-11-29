
from systems.command import args
from data.user import models


class UserMixin(object):

    def generate_schema(self):
        super().get_schema()
        self.schema['user'] = 'str'
        self.schema['user_fields'] = 'dict'


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


    def parse_user_fields(self):
        args.parse_key_values(self.parser, 
            'user_fields',
            'field=value',
            'user fields as key value pairs'
        )

    @property
    def user_fields(self):
        return self.options['user_fields']

   
    @property
    def _user(self):
        return models.User.facade
