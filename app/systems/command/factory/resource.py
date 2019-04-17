from utility.data import ensure_list
from .helpers import *

import re


def ListCommand(parents, base_name,
    facade_name = None,
    search_field = None,
    order_field = None,
    limit_field = None
):
    _parents = ensure_list(parents)
    _facade_name = get_facade(facade_name, base_name)
    _order_field = get_joined_value(order_field, base_name, 'order')
    _limit_field = get_joined_value(order_field, base_name, 'limit')
    _search_field = get_joined_value(search_field, base_name, 'search')

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
        facade = getattr(self, _facade_name)

        if getattr(self, _order_field, None) is not None:
            getattr(self, "parse_{}".format(_order_field))('--order')

        if getattr(self, _limit_field, None) is not None:
            getattr(self, "parse_{}".format(_limit_field))('--limit')

        if getattr(self, _search_field, None) is not None:
            self.parse_flag('or', '--or', 'perform an OR query on input filters')
            getattr(self, "parse_{}".format(_search_field))(True)

        parse_field_names(self)

    def __exec(self):
        filters = {}
        facade = getattr(self, _facade_name)
        queries = getattr(self, _search_field, None)
        if queries:
            joiner = 'OR' if self.options.get('or', False) else 'AND'
            instances = self.search_instances(facade, queries, joiner)
            filters["{}__in".format(facade.pk)] = [ getattr(x, facade.pk) for x in instances ]

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
            self.table(data)
        else:
            self.error('No results', silent = True)

    return type('ListCommand', tuple(_parents), {
        'get_epilog': __get_epilog,
        'parse': __parse,
        'exec': __exec
    })


def GetCommand(parents, base_name,
    facade_name = None,
    name_field = None
):
    _parents = ensure_list(parents)
    _facade_name = get_facade(facade_name, base_name)
    _name_field = get_joined_value(name_field, base_name, 'name')

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
        facade = getattr(self, _facade_name)
        if not name_field:
            getattr(self, "parse_{}".format(_name_field))()
        else:
            self.parse_scope(facade)

        self.parse_dependency(facade)
        parse_field_names(self)

    def __exec(self):
        facade = getattr(self, _facade_name)
        instance = getattr(self, base_name)
        self.table(self.render_display(
            facade,
            instance.name,
            allowed_fields = get_field_names(self)
        ))

    return type('GetCommand', tuple(_parents), {
        'get_epilog': __get_epilog,
        'parse': __parse,
        'exec': __exec
    })


def SaveCommand(parents, base_name,
    provider_name = None,
    provider_subtype = None,
    facade_name = None,
    name_field = None,
    multiple = False,
    fields_field = None,
    save_fields = {},
    pre_methods = {},
    post_methods = {}
):
    _parents = ensure_list(parents)
    _provider_name = get_value(provider_name, base_name)
    _facade_name = get_facade(facade_name, base_name)
    _name_field = get_joined_value(name_field, base_name, 'name')
    _fields_field = get_joined_value(fields_field, base_name, 'fields')

    def __parse(self):
        facade = getattr(self, _facade_name)

        self.parse_test()
        self.parse_force()

        if multiple:
            self.parse_count()
            self.parse_flag('remove', '--rm', 'remove any instances above --count')

        if not facade.provider_relation:
            getattr(self, "parse_{}_provider_name".format(_provider_name))('--provider')

        if not name_field:
            getattr(self, "parse_{}".format(_name_field))()
        else:
            self.parse_scope(facade)

        self.parse_dependency(facade)

        if not fields_field and not save_fields:
            if provider_subtype:
                provider = "{}:{}".format(_provider_name, provider_subtype)
            else:
                provider = _provider_name

            getattr(self, "parse_{}".format(_fields_field))(True, self.get_provider(provider, 'help').field_help)

        if save_fields:
            parse_fields(self, save_fields)

        self.parse_relations(facade)

    def __exec(self):
        facade = getattr(self, _facade_name)
        self.set_scope(facade)

        base_name = getattr(self, _name_field)
        if save_fields:
            fields = get_fields(self, save_fields)
        else:
            fields = getattr(self, _fields_field)

        exec_methods(self, pre_methods)

        def update(name):
            if self.check_exists(facade, name):
                instance = self.get_instance(facade, name)
                instance.provider.update(fields)
            else:
                if getattr(facade.meta, 'provider_relation', None):
                    provider_relation = getattr(self, facade.meta.provider_relation)
                    provider = self.get_provider(facade.provider_name, provider_relation.provider_type)
                else:
                    provider = getattr(self, "{}_provider".format(_provider_name))
                    if provider_subtype:
                        provider = getattr(provider, provider_subtype)

                provider.create(name, fields)

        def remove(name):
            if self.check_exists(facade, name):
                instance = self.get_instance(facade, name)
                options = self.get_scope_filters(instance)
                options['force'] = True
                options[_name_field] = instance.name

                if getattr(facade.meta, 'command_base', None) is not None:
                    command_base = facade.meta.command_base
                else:
                    command_base = facade.name.replace('_', ' ')

                if command_base:
                    self.exec_local("{} rm".format(command_base), options)

        if multiple:
            state_variable = "{}-{}-{}-count".format(facade.name, base_name, facade.get_scope_name())
            existing_count = int(self.get_state(state_variable, 0))
            self.run_list(
                [ "{}{}".format(base_name, x + 1) for x in range(self.count) ],
                update
            )
            if self.options.get('remove', False) and existing_count > self.count:
                self.run_list(
                    [ "{}{}".format(base_name, x + 1) for x in range(self.count, existing_count) ],
                    remove
                )
            self.set_state(state_variable, self.count)
        else:
            update(base_name)

        exec_methods(self, post_methods)

    return type('SaveCommand', tuple(_parents), {
        'parse': __parse,
        'exec': __exec
    })


def RemoveCommand(parents, base_name,
    facade_name = None,
    name_field = None,
    multiple = False,
    pre_methods = {},
    post_methods = {}
):
    _parents = ensure_list(parents)
    _facade_name = get_facade(facade_name, base_name)
    _name_field = get_joined_value(name_field, base_name, 'name')

    def __parse(self):
        facade = getattr(self, _facade_name)
        self.parse_force()
        if not name_field:
            getattr(self, "parse_{}".format(_name_field))()
        else:
            self.parse_scope(facade)

        self.parse_dependency(facade)

    def __confirm(self):
        self.confirmation()

    def __exec(self):
        facade = getattr(self, _facade_name)

        # TODO: For the love of god, find another way!!
        scope_filters = self.set_scope(facade, True)
        if facade.scope_fields and len(facade.scope_fields) > len(scope_filters.keys()):
            return

        base_name = getattr(self, _name_field)
        abstract_name = multiple
        if re.search(r'\d+$', base_name):
            abstract_name = False

        exec_methods(self, pre_methods)

        def remove(name):
            if self.check_exists(facade, name):
                facade_index = self.manager.get_facade_index()
                instance = self.get_instance(facade, name)
                options = self.get_scope_filters(instance)
                options['force'] = self.force

                for child in facade.get_children():
                    sub_facade = facade_index[child]

                    if getattr(sub_facade.meta, 'command_base', None) is not None:
                        command_base = sub_facade.meta.command_base
                    else:
                        command_base = child.replace('_', ' ')

                    if command_base:
                        options = {**options, _name_field: instance.name}
                        self.exec_local("{} clear".format(command_base), options)

                instance.provider.delete()

        if abstract_name:
            state_variable = "{}-{}-{}-count".format(facade.name, base_name, facade.get_scope_name())
            names = list(facade.keys(name__regex="^{}\d+$".format(base_name)))
            self.run_list(names, remove)
            self.delete_state(state_variable)
        else:
            remove(base_name)

        exec_methods(self, post_methods)

    return type('RemoveCommand', tuple(_parents), {
        'parse': __parse,
        'confirm': __confirm,
        'exec': __exec
    })


def ClearCommand(parents, base_name,
    facade_name = None,
    name_field = None,
    pre_methods = {},
    post_methods = {}
):
    _parents = ensure_list(parents)
    _facade_name = get_facade(facade_name, base_name)
    _name_field = get_joined_value(name_field, base_name, 'name')

    def __parse(self):
        facade = getattr(self, _facade_name)
        self.parse_force()
        self.parse_scope(facade)
        self.parse_dependency(facade)

    def __confirm(self):
        self.confirmation()

    def __exec(self):
        facade = getattr(self, _facade_name)
        self.set_scope(facade, True)

        exec_methods(self, pre_methods)
        instances = self.get_instances(facade)

        def remove(instance):
            options = self.get_scope_filters(instance)
            options['force'] = self.force
            options[_name_field] = instance.name

            if getattr(facade.meta, 'command_base', None) is not None:
                command_base = facade.meta.command_base
            else:
                command_base = facade.name.replace('_', ' ')

            if command_base:
                self.exec_local("{} rm".format(command_base), options)

        self.run_list(instances, remove)
        exec_methods(self, post_methods)

    return type('ClearCommand', tuple(_parents), {
        'parse': __parse,
        'confirm': __confirm,
        'exec': __exec
    })


def ResourceCommandSet(parents, base_name,
    facade_name = None,
    provider_name = None,
    provider_subtype = None,
    search_field = None,
    order_field = None,
    limit_field = None,
    name_field = None,
    fields_field = None,
    save_multiple = False,
    save_fields = {},
    save_pre_methods = {},
    save_post_methods = {},
    rm_pre_methods = {},
    rm_post_methods = {},
    clear_pre_methods = {},
    clear_post_methods = {}
):
    return [
        ('list', ListCommand(
            parents, base_name,
            facade_name = facade_name,
            search_field = search_field,
            order_field = order_field,
            limit_field = limit_field
        )),
        ('get', GetCommand(
            parents, base_name,
            facade_name = facade_name,
            name_field = name_field
        )),
        ('save', SaveCommand(
            parents, base_name,
            provider_name = provider_name,
            provider_subtype = provider_subtype,
            facade_name = facade_name,
            multiple = save_multiple,
            name_field = name_field,
            fields_field = fields_field,
            save_fields = save_fields,
            pre_methods = save_pre_methods,
            post_methods = save_post_methods
        )),
        ('rm', RemoveCommand(
            parents, base_name,
            facade_name = facade_name,
            multiple = save_multiple,
            name_field = name_field,
            pre_methods = rm_pre_methods,
            post_methods = rm_post_methods
        )),
        ('clear', ClearCommand(
            parents, base_name,
            facade_name = facade_name,
            name_field = name_field,
            pre_methods = clear_pre_methods,
            post_methods = clear_post_methods
        ))
    ]
