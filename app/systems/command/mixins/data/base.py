from systems.command import args
from utility import text

import re
import copy


class DataMixin(object):
    
    def parse_variable(self, name, optional, type, help_text, value_label = None):
        if optional and isinstance(optional, str):
            if not value_label:
                value_label = name
            
            self.add_schema_field(name,
                args.parse_option(self.parser, name, value_label.upper(), optional, type, help_text, None),
                True
            )
        else:
            self.add_schema_field(name, 
                args.parse_var(self.parser, name, type, help_text, optional), 
                optional
            )

    def parse_variables(self, name, optional, type, help_text, value_label = None):
        if optional and isinstance(optional, str):
            help_text = "{} (comma separated)".format(help_text)

            if not value_label:
                value_label = name

            self.add_schema_field(name,
                args.parse_csv_option(self.parser, name, value_label.upper(), optional, help_text, None),
                True
            )
        else:
            self.add_schema_field(name,
                args.parse_vars(self.parser, name, type, help_text, optional),
                optional
            )

    def parse_fields(self, facade, name, optional = False, excluded_fields = [], help_callback = None, callback_args = [], callback_options = {}):
        if help_callback and callable(help_callback):
            help_text = "\n".join(help_callback(*callback_args, **callback_options))
        else:
            required = [x for x in facade.required if x not in list(excluded_fields)]
            optional = [x for x in facade.optional if x not in excluded_fields]
            help_text = "\n".join(text.wrap("fields as key value pairs\n\nrequirements: {}\n\noptions: {}".format(", ".join(required), ", ".join(optional)), 60))

        self.add_schema_field(name,
            args.parse_key_values(self.parser, name, 'field=VALUE', help_text, optional),
            optional
        )


    def check_available(self, facade, name):
        instance = self.get_instance(facade, name, required = False)
        if instance:
            self.warning("{} {} already exists".format(
                facade.name.title(),
                name
            ))
            return False        
        return True

    def check_exists(self, facade, name):
        instance = self.get_instance(facade, name, required = False)
        if not instance:
            self.warning("{} {} does not exist".format(
                facade.name.title(),
                name
            ))
            return False        
        return True


    def get_instance(self, facade, name, required = True):
        instance = self._get_cache_instance(facade, name)

        if not instance:
            instance = facade.retrieve(name)
            
            if not instance and required:
                self.error("{} {} does not exist".format(facade.name.title(), name))
            else:
                if instance:
                    if not getattr(instance, 'initialize', None) or instance.initialize(self):
                        self._set_cache_instance(facade, instance.name, instance)
                    else:
                        return None
        return instance


    def get_instances(self, facade, names = [], objects = [], groups = [], states = None):
        search_items = []
        instances = []

        if isinstance(names, str):
            names = [names]
        
        if names:
            search_items.extend(names)

        if not isinstance(objects, (list, tuple)):
            objects = [objects]

        if objects:
            search_items.extend(objects)

        if isinstance(groups, str):
            groups = [groups]
        
        for group in groups:
            search_items.extend(facade.field_values('name', groups__name = group))        

        if states and not isinstance(states, (list, tuple)):
            states = [states]

        if not search_items and not names and not objects and not states:
            search_items = facade.all()

        def init_instance(input, state):
            if isinstance(input, str):
                instance = facade.retrieve(input)
            else:
                instance = input
            
            if instance:
                cached = self._get_cache_instance(facade, instance.name)
                
                if not cached:
                    if not getattr(instance, 'initialize', None) or instance.initialize(self):
                        self._set_cache_instance(facade, instance.name, instance)
                    else:
                        instance = None
                else:
                    instance = cached
                
                if instance and (not states or instance.state in states):
                    instances.append(instance)
            else:
                self.error("{} instance {} does not exist".format(facade.name.title(), input))

        self.run_list(search_items, init_instance)
        return instances


    def get_instances_by_reference(self, facade, reference = None, error_on_empty = True, group_facade = None, selection_callback = None):
        results = []

        if reference and reference != 'all':
            matches = re.search(r'^([^\=]+)\s*\=\s*(.+)', reference)

            if matches:
                field = matches.group(1)
                value = matches.group(2)

                if field != 'state':
                    instances = facade.query(**{ field: value })
                    states = None
                else:
                    instances = facade.all()
                    states = [value]
                    
                if len(instances) > 0:
                    results.extend(self.get_instances(facade,
                        objects = list(instances), 
                        states = states
                    ))
            else:
                instance = facade.retrieve(reference)
                found = False
                
                if instance:
                    results.extend(self.get_instances(facade, objects = instance))
                    found = True
                
                if not found and group_facade:
                    group = group_facade.retrieve(reference)
                    if group:
                        results.extend(self.get_instances(facade, groups = reference))
                        found = True
                
                if not found and selection_callback and callable(selection_callback):
                    instances = selection_callback(facade, reference)
                    if instances:
                        results.extend(instances)
        else:
            results.extend(self.get_instances(facade))
        
        if error_on_empty and not results:
            if reference:
                self.warning("No {} instances were found: {}".format(facade.name, reference))
            else:
                self.warning("No {} instances were found".format(facade.name))
        
        return results


    def facade(self, facade):
        if getattr(self, '_facade_cache', None) is None:
            self._facade_cache = {}
        
        if not self._facade_cache.get(facade.name, None):
            self._facade_cache[facade.name] = copy.deepcopy(facade)

        return self._facade_cache[facade.name]


    def _parse_add_remove_names(self, names):
        add_names = []
        remove_names = []
        
        if names:
            for name in names:
                name = re.sub(r'\s+', '', name) 
                matches = re.search(r'^-(.*)$', name)
                if matches:
                    remove_names.append(matches.group(1))
                else:
                    name = name[1:] if name[0] == '+' else name
                    add_names.append(name)
        
        return (add_names, remove_names)


    def _init_instance_cache(self, facade):
        cache_variable = "_data_{}_cache".format(facade.name)

        if not getattr(self, cache_variable, None):
            setattr(self, cache_variable, {})

        return cache_variable
        
    def _get_cache_instance(self, facade, name):
        cache_variable = self._init_instance_cache(facade)
        return getattr(self, cache_variable).get(name, None)

    def _set_cache_instance(self, facade, name, instance):
        cache_variable = self._init_instance_cache(facade)
        getattr(self, cache_variable)[name] = instance
