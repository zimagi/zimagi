
from systems.command import args
from data.user import models
from utility import text


class UserMixin(object):

    def parse_user(self, optional = False):
        name = 'user'
        help_text = 'environment user name'

        self._data_user = None
        self.add_schema_field(name,
            args.parse_var(self.parser, name, str, help_text, optional),
            optional
        )

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


    def parse_group(self, optional = False):
        name = 'group'
        help_text = 'environment user group'

        self._data_group = None
        self.add_schema_field(name,
            args.parse_var(self.parser, name, str, help_text, optional),
            optional
        )

    @property
    def group_name(self):
        return self.options['group']

    @property
    def group(self):
        if not self._data_group:
            self._data_group = self._group.retrieve(self.group_name)

            if not self._data_group:
                self.error("Group {} does not exist".format(self.group_name))
        
        return self._data_group


    def parse_groups(self, optional = False):
        name = 'groups'
        help_text = 'environment user groups'

        self._data_groups = []
        self.add_schema_field(name,
            args.parse_vars(self.parser, name, 'group', str, help_text, optional),
            optional
        )

    @property
    def group_names(self):
        return self.options['groups']

    @property
    def groups(self):
        if not self._data_groups:
            for name in self.group_names:
                group = self._group.retrieve(name)

                if not group:
                    self.error("Group {} does not exist".format(name))

                self._data_groups.append(group)
        
        return self._data_groups


    def parse_user_fields(self, optional = False):
        name = 'user_fields'

        excluded_fields = ('password', 'date_joined', 'last_login', 'is_superuser', 'is_staff', 'is_active')
        required = [x for x in self._user.required if x not in excluded_fields]
        optional = [x for x in self._user.optional if x not in excluded_fields]
        help_text = "\n".join(text.wrap("user fields as key value pairs\n\ncreate required: {}\n\nupdate available: {}".format(", ".join(required), ", ".join(optional)), 60))

        self.add_schema_field(name,
            args.parse_key_values(self.parser, name, 'field=value', help_text, optional),
            optional
        )

    @property
    def user_fields(self):
        return self.options['user_fields']

   
    @property
    def _user(self):
        return models.User.facade
   
    @property
    def _group(self):
        return models.Group.facade
