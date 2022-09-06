from utility.data import ensure_list
from utility.python import create_class
from .helpers import *


def ListCommand(parents, base_name, facade_name,
    view_roles = None
):
    _parents = ensure_list(parents)
    _facade_name = get_facade(facade_name)
    _order_field = get_joined_value(base_name, 'order')
    _limit_field = get_joined_value(base_name, 'limit')

    def __get_priority(self):
        return 5

    def __groups_allowed(self):
        from settings.roles import Roles
        return [ Roles.admin ] + ensure_list(view_roles)

    def __get_epilog(self):
        facade = getattr(self, _facade_name)
        variable = "{}_list_fields".format(facade.name)
        fields = [ x.name for x in reversed(facade.meta.get_fields()) ]

        return 'field display config: {}\n\n> {} fields: {}'.format(
            self.header_color(variable),
            facade.name,
            self.notice_color(", ".join(fields))
        )

    def __parse(self):
        getattr(self, "parse_{}".format(_order_field))('--order')
        getattr(self, "parse_{}".format(_limit_field))('--limit')

        self.parse_search(True)
        parse_field_names(self)

    def __exec(self):
        filters = {}
        facade = getattr(self, _facade_name)
        queries = self.search_queries
        if queries:
            instances = self.search_instances(facade, queries, self.search_join)
            filters["{}__in".format(facade.pk)] = [ getattr(x, facade.pk) for x in instances ]

        count = facade.count(**filters)

        order_by = getattr(self, _order_field, None)
        if order_by:
            facade.set_order(order_by)

        limit = getattr(self, _limit_field, None)
        if limit:
            facade.set_limit(limit)

        data = self.render_list(
            facade,
            filters = filters,
            allowed_fields = get_field_names(self)
        )
        if data:
            self.info('')
            self.data(" {} results".format(facade.name.capitalize()), count, 'total')
            if limit:
                self.data(' Showing', min(len(data) - 1, limit), 'count')
            self.table(data, 'results')
        else:
            self.error('No results', silent = True)

    def __str__(self):
        return "List <{}>".format(base_name)

    attributes = {
        '_resource': facade_name,
        'get_priority': __get_priority,
        'get_epilog': __get_epilog,
        'parse': __parse,
        'exec': __exec,
        '__str__': __str__
    }
    if view_roles:
        attributes['groups_allowed'] = __groups_allowed

    return create_class(
        "commands.{}.list".format(facade_name),
        'ListCommand',
        parents = _parents,
        attributes = attributes
    )


def GetCommand(parents, base_name, facade_name,
    view_roles = None
):
    _parents = ensure_list(parents)
    _facade_name = get_facade(facade_name)
    _key_field = get_joined_value(base_name, 'key')

    def __get_priority(self):
        return 10

    def __groups_allowed(self):
        from settings.roles import Roles
        return [ Roles.admin ] + ensure_list(view_roles)

    def __get_epilog(self):
        facade = getattr(self, _facade_name)
        variable = "{}_display_fields".format(facade.name)
        fields = [ x.name for x in reversed(facade.meta.get_fields()) ]

        return 'field display config: {}\n\n> {} fields: {}'.format(
            self.header_color(variable),
            facade.name,
            self.notice_color(", ".join(fields))
        )

    def __parse(self):
        getattr(self, "parse_{}".format(_key_field))()
        parse_field_names(self)

    def __exec(self):
        facade = getattr(self, _facade_name)
        instance = getattr(self, base_name)
        self.table(self.render_display(
            facade,
            getattr(instance, facade.key()),
            allowed_fields = get_field_names(self)
        ), 'data', row_labels = True)

    def __str__(self):
        return "Get <{}>".format(base_name)

    attributes = {
        '_resource': facade_name,
        'get_priority': __get_priority,
        'get_epilog': __get_epilog,
        'parse': __parse,
        'exec': __exec,
        '__str__': __str__
    }
    if view_roles:
        attributes['groups_allowed'] = __groups_allowed

    return create_class(
        "commands.{}.get".format(facade_name),
        'GetCommand',
        parents = _parents,
        attributes = attributes
    )


def SaveCommand(parents, base_name, facade_name,
    provider_name = None,
    edit_roles = None,
    save_fields = None
):
    if save_fields is None:
        save_fields = {}

    _parents = ensure_list(parents)
    _facade_name = get_facade(facade_name)
    _key_field = get_joined_value(base_name, 'key')
    _fields_field = get_joined_value(base_name, 'fields')

    def __get_priority(self):
        return 15

    def __groups_allowed(self):
        from settings.roles import Roles
        return [ Roles.admin ] + ensure_list(edit_roles)

    def __parse(self):
        facade = getattr(self, _facade_name)
        key_options = {}

        if provider_name:
            self.parse_test()
            self.parse_force()
            getattr(self, "parse_{}_provider_name".format(provider_name))('--provider')

        from data.base.id_resource import IdentifierResourceBase
        if issubclass(facade.model, IdentifierResourceBase) and facade.key() == facade.pk:
            key_options['optional'] = '--id'

        getattr(self, "parse_{}".format(_key_field))(**key_options)

        if not save_fields:
            help_callback = self.get_provider(provider_name, 'help').field_help if provider_name else None
            getattr(self, "parse_{}".format(_fields_field))(True, help_callback)
        else:
            parse_fields(self, save_fields)

        self.parse_relations(facade)

    def __exec(self):
        facade = getattr(self, _facade_name)
        self.set_scope(facade)

        key = getattr(self, _key_field)
        if save_fields:
            fields = get_fields(self, save_fields)
        else:
            fields = getattr(self, _fields_field)

        if self.get_instance(facade, key, required = False):
            provider_type = None
            if getattr(self, "check_{}_provider_name".format(provider_name))():
                provider_type = getattr(self, "{}_provider_name".format(provider_name), None)
        else:
            provider_type = getattr(self, "{}_provider_name".format(provider_name), None)

        self.save_instance(
            facade, key,
            provider_type = provider_type,
            fields = fields,
            relations = self.get_relations(facade),
            relation_key = True
        )

    def __str__(self):
        return "Save <{}>".format(base_name)

    attributes = {
        '_resource': facade_name,
        'get_priority': __get_priority,
        'parse': __parse,
        'exec': __exec,
        '__str__': __str__
    }
    if edit_roles:
        attributes['groups_allowed'] = __groups_allowed

    return create_class(
        "commands.{}.save".format(facade_name),
        'SaveCommand',
        parents = _parents,
        attributes = attributes
    )


def RemoveCommand(parents, base_name, facade_name,
    edit_roles = None
):
    _parents = ensure_list(parents)
    _facade_name = get_facade(facade_name)
    _key_field = get_joined_value(base_name, 'key')

    def __get_priority(self):
        return 20

    def __groups_allowed(self):
        from settings.roles import Roles
        return [ Roles.admin ] + ensure_list(edit_roles)

    def __parse(self):
        self.parse_force()
        getattr(self, "parse_{}".format(_key_field))()

    def __confirm(self):
        self.confirmation()

    def __exec(self):
        facade = getattr(self, _facade_name)
        self.set_scope(facade, True)

        self.remove_instance(
            facade,
            getattr(self, _key_field)
        )

    def __str__(self):
        return "Remove <{}>".format(base_name)

    attributes = {
        '_resource': facade_name,
        'get_priority': __get_priority,
        'parse': __parse,
        'confirm': __confirm,
        'exec': __exec,
        '__str__': __str__
    }
    if edit_roles:
        attributes['groups_allowed'] = __groups_allowed

    return create_class(
        "commands.{}.remove".format(facade_name),
        'RemoveCommand',
        parents = _parents,
        attributes = attributes
    )


def ClearCommand(parents, base_name, facade_name,
    edit_roles = None
):
    _parents = ensure_list(parents)
    _facade_name = get_facade(facade_name)
    _key_field = get_joined_value(base_name, 'key')

    def __get_priority(self):
        return 25

    def __groups_allowed(self):
        from settings.roles import Roles
        return [ Roles.admin ] + ensure_list(edit_roles)

    def __parse(self):
        facade = getattr(self, _facade_name)
        self.parse_search(True)
        self.parse_force()
        self.parse_scope(facade)

    def __confirm(self):
        self.confirmation()

    def __exec(self):
        facade = getattr(self, _facade_name)
        self.set_scope(facade, True)

        instances = self.search_instances(facade, self.search_queries, self.search_join)

        def remove(instance):
            options = self.get_scope_filters(instance)
            options['force'] = self.force
            options['verbosity'] = self.verbosity
            options[_key_field] = getattr(instance, facade.key())

            if getattr(facade.meta, 'command_base', None) is not None:
                command_base = facade.meta.command_base
            else:
                command_base = facade.name.replace('_', ' ')

            if command_base:
                self.exec_local("{} remove".format(command_base), options)

        self.run_list(instances, remove)
        self.success("Successfully cleared all {}".format(facade.plural))

    def __str__(self):
        return "Clear <{}>".format(base_name)

    attributes = {
        '_resource': facade_name,
        'get_priority': __get_priority,
        'parse': __parse,
        'confirm': __confirm,
        'exec': __exec,
        '__str__': __str__
    }
    if edit_roles:
        attributes['groups_allowed'] = __groups_allowed

    return create_class(
        "commands.{}.clear".format(facade_name),
        'ClearCommand',
        parents = _parents,
        attributes = attributes
    )


def ResourceCommandSet(command, parents, base_name, facade_name,
    provider_name = None,
    save_fields = None,
    edit_roles = None,
    view_roles = None,
    allow_list = True,
    allow_access = True,
    allow_update = True,
    allow_remove = True,
    allow_clear = True
):
    if save_fields is None:
        save_fields = {}

    if edit_roles:
        edit_roles = ensure_list(edit_roles)
        if view_roles:
            view_roles = ensure_list(view_roles) + edit_roles
        else:
            view_roles = edit_roles

    if allow_list:
        command['list'] = ListCommand(
            parents, base_name, facade_name,
            view_roles = view_roles
        )
    if allow_access:
        command['get'] = GetCommand(
            parents, base_name, facade_name,
            view_roles = view_roles
        )
    if allow_update:
        command['save'] = SaveCommand(
            parents, base_name, facade_name,
            provider_name = provider_name,
            edit_roles = edit_roles,
            save_fields = save_fields
        )
    if allow_remove:
        command['remove'] = RemoveCommand(
            parents, base_name, facade_name,
            edit_roles = edit_roles
        )
        if allow_clear:
            command['clear'] = ClearCommand(
                parents, base_name, facade_name,
                edit_roles = edit_roles
            )
    return command
