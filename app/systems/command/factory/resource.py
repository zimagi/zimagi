from systems.command import types, mixins
from utility.data import ensure_list
from .helpers import *

import re


def ListCommand(parents, base_name,
    facade_name = None,
    search_field = None,
    order_field = None,
    scopes = {}
):
    _parents = ensure_list(parents)
    _facade_name = get_facade(facade_name, base_name)
    _order_field = get_joined_value(order_field, base_name, 'order')
    _search_field = get_joined_value(search_field, base_name, 'search')
 
    def _parse(self):
        if getattr(self, _order_field, None) is not None:
            getattr(self, "parse_{}".format(_order_field))('--order')
        
        if getattr(self, _search_field, None) is not None:
            self.parse_flag('or', '--or', 'perform an OR query on input filters')
            getattr(self, "parse_{}".format(_search_field))(True)
        
        parse_fields(self, scopes)
    
    def _exec(self):
        set_scopes(self, scopes)

        facade = getattr(self, _facade_name)
        filters = {}
        
        queries = getattr(self, _search_field, None)
        if queries:
            joiner = 'OR' if self.options.get('or', False) else 'AND'
            instances = self.search_instances(facade, queries, joiner)
            filters["{}__in".format(facade.key())] = [ getattr(x, facade.key()) for x in instances ]

        order_by = getattr(self, _order_field, None)
        if order_by:
            facade.set_order(order_by)

        data = facade.render_list(self, filters = filters)
        if data:
            self.table(data)
    
    return type('ListCommand', tuple(_parents), {
        'parse': _parse,
        'exec': _exec
    })


def GetCommand(parents, base_name, 
    facade_name = None,
    name_field = None,
    scopes = {}
):
    _parents = ensure_list(parents)
    _facade_name = get_facade(facade_name, base_name)
    _name_field = get_joined_value(name_field, base_name, 'name')

    def _parse(self):
        if not name_field:
            getattr(self, "parse_{}".format(_name_field))()
        
        parse_fields(self, scopes)

    def _exec(self):
        set_scopes(self, scopes)

        facade = getattr(self, _facade_name)
        name = getattr(self, _name_field)

        if self.get_instance(facade, name):
            self.table(facade.render_display(self, name))
    
    return type('GetCommand', tuple(_parents), {
        'parse': _parse,
        'exec': _exec
    })


def SaveCommand(parents, base_name,
    provider_name = None,
    provider_subtype = None,
    facade_name = None,
    name_field = None,
    fields_field = None,
    save_fields = {},
    relations = {},
    scopes = {},
    pre_methods = {},
    post_methods = {}
):
    _parents = ensure_list(parents)
    _provider_name = get_value(provider_name, base_name)
    _facade_name = get_facade(facade_name, base_name)
    _name_field = get_joined_value(name_field, base_name, 'name')
    _fields_field = get_joined_value(fields_field, base_name, 'fields')

    def _parse(self):
        self.parse_test()
        self.parse_force()

        getattr(self, "parse_{}_provider_name".format(_provider_name))('--provider')
        
        if not name_field:
            getattr(self, "parse_{}".format(_name_field))()

        if not fields_field and not save_fields:        
            getattr(self, "parse_{}".format(_fields_field))(True, self.get_provider(_provider_name, 'help').field_help)
        
        if save_fields:
            parse_fields(self, save_fields)

        parse_fields(self, scopes)
        parse_fields(self, relations)

    def _exec(self):
        set_scopes(self, scopes)

        facade = getattr(self, _facade_name)
        name = getattr(self, _name_field)
        related_data = get_fields(self, relations)

        if save_fields:
            fields = get_fields(self, save_fields)
        else:
            fields = getattr(self, _fields_field)
        
        exec_methods(self, pre_methods)

        if self.check_exists(facade, name):
            instance = self.get_instance(facade, name)
            instance.provider.update(fields, **related_data)
        else:
            provider = getattr(self, "{}_provider".format(_provider_name))
            if provider_subtype:
                provider = getattr(provider, provider_subtype)    
            provider.create(name, fields, **related_data)
        
        exec_methods(self, post_methods)
    
    return type('SaveCommand', tuple(_parents), {
        'parse': _parse,
        'exec': _exec
    })


def RemoveCommand(parents, base_name,
    facade_name = None,
    name_field = None,
    children = [],
    scopes = {},
    pre_methods = {},
    post_methods = {}
):
    _parents = ensure_list(parents)
    _facade_name = get_facade(facade_name, base_name)
    _name_field = get_joined_value(name_field, base_name, 'name')

    def _parse(self):
        self.parse_force()

        if not name_field:
            getattr(self, "parse_{}".format(_name_field))()
        
        parse_fields(self, scopes)

    def _confirm(self):
        self.confirmation()       

    def _exec(self):
        set_scopes(self, scopes)
        facade = getattr(self, _facade_name)
        name = getattr(self, _name_field)

        exec_methods(self, pre_methods)
        if self.check_exists(facade, name):
            instance = self.get_instance(facade, name)
            options = { 'force': self.force }

            for scope_name, info in scopes.items():
                scope_field = "{}_name".format(scope_name)
                options[scope_field] = get_scope(self, scope_name, scopes)

            for child in children:
                command_base = " ".join(child.split('_'))
                self.exec_local("{} clear".format(command_base), options)
            
            instance.provider.delete()
            exec_methods(self, post_methods)
    
    return type('RemoveCommand', tuple(_parents), {
        'parse': _parse,
        'confirm': _confirm,
        'exec': _exec
    })


def ClearCommand(parents, base_name, 
    facade_name = None,
    name_field = None,
    command_base = None,
    scopes = {},
    pre_methods = {},
    post_methods = {}
):
    parents = ensure_list(parents)
    facade_name = get_facade(facade_name, base_name)
    name_field = get_joined_value(name_field, base_name, 'name')
    command_base = get_value(command_base, " ".join(base_name.split('_')))
    
    def _parse(self):
        self.parse_force()
        parse_fields(self, scopes)
    
    def _confirm(self):
        self.confirmation()       

    def _exec(self):
        set_scopes(self, scopes)
        facade = getattr(self, facade_name)

        exec_methods(self, pre_methods)
        instances = self.get_instances(facade)
        
        def remove(instance, state):
            options = { 'force': self.force } 
            options[name_field] = instance.name 
            
            for scope_name, info in scopes.items():
                scope_field = "{}_name".format(scope_name)
                options[scope_field] = get_scope(instance, scope_name, scopes)

            self.exec_local("{} rm".format(command_base), options)
        
        self.run_list(instances, remove)
        exec_methods(self, post_methods)
    
    return type('ClearCommand', tuple(parents), {
        'parse': _parse,
        'confirm': _confirm,
        'exec': _exec
    })


def ResourceCommands(parents, base_name,
    facade_name = None,
    provider_name = None,
    provider_subtype = None,
    search_field = None,
    order_field = None,
    name_field = None,
    fields_field = None,
    save_fields = {},
    relations = {},
    children = [],
    scopes = {},
    command_base = None,
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
            scopes = scopes
        )),
        ('get', GetCommand(
            parents, base_name,
            facade_name = facade_name,
            name_field = name_field,
            scopes = scopes
        )),
        ('save', SaveCommand(
            parents, base_name,
            provider_name = provider_name,
            provider_subtype = provider_subtype,
            facade_name = facade_name,
            name_field = name_field,
            fields_field = fields_field,
            save_fields = save_fields,
            relations = relations,
            scopes = scopes,
            pre_methods = save_pre_methods,
            post_methods = save_post_methods
        )),
        ('rm', RemoveCommand(
            parents, base_name,
            facade_name = facade_name,
            name_field = name_field,
            children = children,
            scopes = scopes,
            pre_methods = rm_pre_methods,
            post_methods = rm_post_methods
        )),
        ('clear', ClearCommand(
            parents, base_name,
            facade_name = facade_name,
            name_field = name_field,
            command_base = command_base,
            scopes = scopes,
            pre_methods = clear_pre_methods,
            post_methods = clear_post_methods
        ))
    ]
