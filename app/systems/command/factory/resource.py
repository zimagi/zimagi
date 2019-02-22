from systems.command import types, mixins
from utility.data import ensure_list
from .helpers import *

import re


def ListCommand(parents, base_name,
    facade_name = None,
    fields = [], 
    relations = [],
    scopes = {}
):
    parents = [
        mixins.op.ListMixin, 
    ] + ensure_list(parents)

    facade_name = get_facade(facade_name, base_name)

  
    def _parse(self):
        parse_scopes(self, scopes)
    
    def _exec(self):
        set_scopes(self, scopes)
        facade = getattr(self, facade_name)
                
        def process(op, info, key_index):
            if op == 'label':
                if relations:
                    info.extend([ x.title() for x in relations ])
            else:
                instance = self.get_instance(facade, info[key_index])

                for relation in relations:
                    items = []
                    for sub_instance in getattr(instance, relation).all():
                        items.append(str(sub_instance))
                    info.append("\n".join(items))

        self.exec_processed_list(facade, process, fields)
    
    return type('ListCommand', tuple(parents), {
        'parse': _parse,
        'exec': _exec
    })


def GetCommand(parents, base_name, 
    facade_name = None,
    name_field = None,
    scopes = {}
):
    parents = [
        mixins.op.GetMixin, 
    ] + ensure_list(parents)

    facade_name = get_facade(facade_name, base_name)
    name_field = get_joined_value(name_field, base_name, 'name')


    def _parse(self):
        getattr(self, "parse_{}".format(name_field))()
        parse_scopes(self, scopes)

    def _exec(self):
        set_scopes(self, scopes)
        self.exec_get(
            getattr(self, facade_name), 
            getattr(self, name_field)
        )
    
    return type('GetCommand', tuple(parents), {
        'parse': _parse,
        'exec': _exec
    })


def SaveCommand(parents, base_name,
    provider_name = None,
    provider_subtype = None,
    facade_name = None,
    name_field = None,
    fields_field = None,
    scopes = {}
):
    parents = ensure_list(parents)
    provider_name = get_value(provider_name, base_name)
    facade_name = get_facade(facade_name, base_name)
    name_field = get_joined_value(name_field, base_name, 'name')
    fields_field = get_joined_value(fields_field, base_name, 'fields')


    def _parse(self):
        self.parse_test()
        self.parse_force()

        getattr(self, "parse_{}_provider_name".format(provider_name))('--provider')
        getattr(self, "parse_{}".format(name_field))()
        getattr(self, "parse_{}".format(fields_field))(True, self.get_provider(provider_name, 'help').field_help)
        parse_scopes(self, scopes)

    def _exec(self):
        set_scopes(self, scopes)
        facade = getattr(self, facade_name)
        
        if self.check_exists(facade, getattr(self, name_field)):
            getattr(self, base_name).provider.update(
                getattr(self, fields_field)
            )
        else:
            provider = getattr(self, "{}_provider".format(provider_name))
            if provider_subtype:
                provider = getattr(provider, provider_subtype)
            
            provider.create(
                getattr(self, name_field), 
                getattr(self, fields_field)
            )
    
    return type('SaveCommand', tuple(parents), {
        'parse': _parse,
        'exec': _exec
    })


def RemoveCommand(parents, base_name, 
    facade_name = None,
    name_field = None,
    relations = [],
    scopes = {}
):
    parents = ensure_list(parents)
    facade_name = get_facade(facade_name, base_name)
    name_field = get_joined_value(name_field, base_name, 'name')


    def _parse(self):
        self.parse_force()

        getattr(self, "parse_{}".format(name_field))()
        parse_scopes(self, scopes)

    def _confirm(self):
        self.confirmation()       

    def _exec(self):
        set_scopes(self, scopes)
        facade = getattr(self, facade_name)
                
        if self.check_exists(facade, getattr(self, name_field)):
            options = { 'force': self.force }

            for scope_name, info in scopes.items():
                scope_field = "{}_name".format(scope_name)
                options[scope_field] = get_scope(self, scope_name, scopes)

            for relation in relations:
                command_base = " ".join(relation.split('_'))
                self.exec_local("{} clear".format(command_base), options)
            
            getattr(self, base_name).provider.delete()
    
    return type('RemoveCommand', tuple(parents), {
        'parse': _parse,
        'confirm': _confirm,
        'exec': _exec
    })


def ClearCommand(parents, base_name, 
    facade_name = None,
    name_field = None,
    command_base = None,
    scopes = {}
):
    parents = ensure_list(parents)
    facade_name = get_facade(facade_name, base_name)
    name_field = get_joined_value(name_field, base_name, 'name')
    command_base = get_value(command_base, " ".join(base_name.split('_')))
    

    def _parse(self):
        self.parse_force()
        parse_scopes(self, scopes)
    
    def _confirm(self):
        self.confirmation()       

    def _exec(self):
        set_scopes(self, scopes)
        facade = getattr(self, facade_name)
        instances = self.get_instances(facade)
        
        def remove(instance, state):
            options = { 'force': self.force } 
            options[name_field] = instance.name 
            
            for scope_name, info in scopes.items():
                scope_field = "{}_name".format(scope_name)
                options[scope_field] = get_scope(instance, scope_name, scopes)

            self.exec_local("{} rm".format(command_base), options)
        
        self.run_list(instances, remove)
    
    return type('ClearCommand', tuple(parents), {
        'parse': _parse,
        'confirm': _confirm,
        'exec': _exec
    })


def ResourceCommands(parents, base_name,
    facade_name = None,
    provider_name = None,
    provider_subtype = None,
    name_field = None,
    fields_field = None,
    list_fields = [], 
    relations = [],
    scopes = {},
    command_base = None
):
    return [
        ('list', ListCommand(
            parents, base_name,
            facade_name = facade_name,
            fields = list_fields,
            relations = relations,
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
            scopes = scopes
        )),
        ('rm', RemoveCommand(
            parents, base_name,
            facade_name = facade_name,
            name_field = name_field,
            relations = relations,
            scopes = scopes
        )),
        ('clear', ClearCommand(
            parents, base_name,
            facade_name = facade_name,
            name_field = name_field,
            command_base = command_base,
            scopes = scopes
        ))
    ]
