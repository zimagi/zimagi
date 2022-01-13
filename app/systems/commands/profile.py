from collections import OrderedDict

from systems.models.base import BaseModel
from plugins.parser.config import Provider as ConfigParser
from utility.data import ensure_list, clean_dict, format_value, prioritize

import re
import copy
import json
import yaml


noalias_dumper = yaml.dumper.SafeDumper
noalias_dumper.ignore_aliases = lambda self, data: True


class BaseProfileComponent(object):

    def __init__(self, name, profile):
        self.name = name
        self.profile = profile
        self.command = profile.command
        self.manager = self.command.manager
        self.test = False

    def priority(self):
        return 10

    def facade_name(self):
        return self.name


    def ensure_module_config(self):
        # Override in subclass if needed
        return False


    def skip_run(self):
        # Override in subclass if needed
        return False

    def run(self, name, config):
        # Override in subclass
        pass


    def skip_destroy(self):
        # Override in subclass if needed
        return False

    def destroy(self, name, config):
        # Override in subclass
        pass


    def get_names(self, relation):
        return [ getattr(x, x.facade.key()) for x in relation.all() ]

    def get_info(self, name, config):
        return self.profile.get_info(name, config)

    def pop_info(self, name, config):
        return self.profile.pop_info(name, config)

    def get_value(self, name, config):
        return self.profile.get_value(name, config)

    def pop_value(self, name, config):
        return self.profile.pop_value(name, config)

    def get_values(self, name, config):
        return self.profile.get_values(name, config)

    def pop_values(self, name, config):
        return self.profile.pop_values(name, config)

    def interpolate(self, config, **replacements):
        return self.profile.interpolate(config, replacements)

    def get_variables(self, instance, variables = None):
        if not variables:
            variables = {}

        return self.profile.get_variables(instance, variables)


    def exec(self, command, **parameters):
        self.command.exec_local(command, parameters)

    def run_list(self, elements, processor):
        self.command.run_list(elements, processor)


class CommandProfile(object):

    def __init__(self, module, name = None, data = None):
        if not data:
            data = {}

        self.name = name
        self.module = module
        self.command = module.command
        self.manager = self.command.manager
        self.data = data
        self.components = []


    def get_component_names(self, filter_method = None):
        return self.manager.index.load_component_names(self, filter_method)


    def initialize(self, operation, config, components, display_only):
        self.components = components

        self.init_config(config)
        self.load_parents()
        self.data = self.get_schema()

        if display_only:
            self.display_schema(operation)
            return False
        return True


    def get_config(self):
        return self.data.get('config', {})

    def set_config(self, config):
        self.data['config'] = self.interpolate_config(config)


    def init_config(self, dynamic_config):
        for stored_config in self.command.get_instances(self.command._config):
            ConfigParser.runtime_variables[stored_config.name] = stored_config.value

        if isinstance(dynamic_config, dict):
            for name, value in dynamic_config.items():
                ConfigParser.runtime_variables[name] = value


    def interpolate_config(self, input_config, **options):
        config = {}
        for name, value in input_config.items():
            config[name] = self.interpolate_config_value(value, **options)
            if name not in ConfigParser.runtime_variables:
                ConfigParser.runtime_variables[name] = config[name]
        return config

    def interpolate_config_value(self, value, **options):
        value = self.command.options.interpolate(value, **options)
        return value


    def load_parents(self):
        self.parents = []

        self.set_config(self.get_config())

        if 'parents' in self.data:
            parents = self.data.pop('parents')
            for parent in reversed(ensure_list(parents)):
                module = self.module.instance

                if isinstance(parent, str):
                    profile_name = self.interpolate_config_value(parent)
                else:
                    profile_name = self.interpolate_config_value(parent['profile'])
                    if 'module' in parent:
                        module_name = self.interpolate_config_value(parent['module'])
                        if module_name != 'self':
                            module = self.get_module(module_name)

                self.parents.insert(0,
                    module.provider.get_profile(profile_name)
                )

            for profile in reversed(self.parents):
                profile.load_parents()


    def get_schema(self):
        schema = {'config': {}}

        for profile in self.parents:
            parent_schema = profile.get_schema()
            self.merge_schema(schema, parent_schema)

        self.merge_schema(schema, self.data)

        for component in self.get_component_names('ensure_module_config'):
            if component in schema:
                for name, component_config in schema[component].items():
                    if '_module' not in component_config:
                        component_config['_module'] = self.module.instance.name

        for name, value in schema['config'].items():
            if name in ConfigParser.runtime_variables:
                schema['config'][name] = ConfigParser.runtime_variables[name]

        return schema


    def display_schema(self, operation):
        self.command.info('')

        component_map = self.manager.index.load_components(self)
        for priority, component_list in sorted(component_map.items(), reverse = (operation == 'destroy')):
            def run_component(component):
                rendered_instances = OrderedDict()

                def component_process(name):
                    instance_config = self.data[component.name][name]
                    if self.include_instance(name, instance_config):
                        name = self.command.options.interpolate(name)

                        if 'config' in instance_config:
                            getattr(component, operation)(name, instance_config)

                        rendered_instances[name] = self.interpolate_config_value(instance_config,
                            config = 'query',
                            config_value = False,
                            function_suppress = '^\s*\<[^\>]+\>\s*$'
                        )
                if ((operation == 'run' and not component.skip_run()) \
                    or (operation == 'destroy' and not component.skip_destroy())) \
                    and self.include(component.name):

                    instance_map = self.order_instances(self.expand_instances(component.name), True)
                    for priority, names in sorted(instance_map.items()):
                        self.command.run_list(names, component_process)

                    self.command.info(yaml.dump(
                        { component.name: rendered_instances },
                        Dumper = noalias_dumper
                    ))

            self.command.run_list(component_list, run_component)
            if priority == 0:
                self.command.options.initialize(True)

        if self.include('profile'):
            component = self.manager.index.load_component(self, 'profile')
            profiles = self.expand_instances(component.name, self.data)

            for profile, config in profiles.items():
                if self.include_instance(profile, config):
                    getattr(component, operation)(profile, config, True)


    def merge_schema(self, schema, data):
        for key, value in data.items():
            if isinstance(value, dict):
                schema.setdefault(key, {})
                self.merge_schema(schema[key], value)
            else:
                schema[key] = value


    def run(self, components = None, config = None, display_only = False, plan = False):
        if not components:
            components = []
        if not config:
            config = {}

        self.command.data("Running profile:", "{}:{}".format(self.module.instance.name, self.name), 'profile_name')

        if self.initialize('run', config, components, display_only):
            component_map = self.manager.index.load_components(self)
            for priority, component_list in sorted(component_map.items()):
                def run_component(component):
                    if not component.skip_run() and self.include(component.name):
                        data = copy.deepcopy(self.data)
                        instance_map = self.order_instances(self.expand_instances(component.name, data))
                        component.test = plan

                        def component_process(name):
                            instance_config = copy.deepcopy(data[component.name][name])
                            if self.include_instance(name, instance_config):
                                if isinstance(instance_config, dict):
                                    instance_config.pop('_keep', None)

                                name = self.command.options.interpolate(name)
                                component.run(name, instance_config)

                        for priority, names in sorted(instance_map.items()):
                            self.command.run_list(names, component_process)

                self.command.run_list(component_list, run_component)
                if priority == 0:
                    self.command.options.initialize(True)


    def destroy(self, components = None, config = None, display_only = False):
        if not components:
            components = []
        if not config:
            config = {}

        self.command.data("Destroying profile:", "{}:{}".format(self.module.instance.name, self.name), 'profile_name')

        if self.initialize('destroy', config, components, display_only):
            component_map = self.manager.index.load_components(self)
            for priority, component_list in sorted(component_map.items(), reverse = True):
                def run_component(component):
                    if not component.skip_destroy() and self.include(component.name):
                        data = copy.deepcopy(self.data)
                        instance_map = self.order_instances(self.expand_instances(component.name, data))

                        def component_process(name):
                            instance_config = copy.deepcopy(data[component.name][name])
                            if self.include_instance(name, instance_config):
                                if not isinstance(instance_config, dict) or not instance_config.pop('_keep', False):
                                    name = self.command.options.interpolate(name)
                                    component.destroy(name, instance_config)

                        for priority, names in sorted(instance_map.items()):
                            self.command.run_list(names, component_process)

                self.command.run_list(component_list, run_component)


    def expand_instances(self, component_name, data = None):
        instance_data = copy.deepcopy(self.data if data is None else data)
        instance_map = {}

        def get_replacements(info, replacements, keys = None):
            if keys is None:
                keys = []

            tag = ".".join(keys) if keys else 'value'

            if isinstance(info, dict):
                for key, value in info.items():
                    get_replacements(value, replacements, keys + [str(key)])
            elif isinstance(info, (list, tuple)):
                replacements["<<{}.*>>".format(tag)] = info
                replacements["<<>{}.*>>".format(tag)] = ",".join(info)
                for index, value in enumerate(info):
                    get_replacements(value, replacements, keys + [str(index)])
            else:
                replacements["<<{}>>".format(tag)] = info

            return replacements

        def substitute_config(config, replacements):
            if isinstance(config, dict):
                config = copy.deepcopy(config)
                for key, value in config.items():
                    config[key] = substitute_config(value, replacements)
            elif isinstance(config, (list, tuple)):
                config = copy.deepcopy(config)
                for index, value in enumerate(config):
                    config[index] = substitute_config(value, replacements)
            else:
                for token in replacements.keys():
                    if str(config) == token:
                        config = replacements[token]
                    else:
                        replacement = replacements[token]
                        if isinstance(replacements[token], (list, tuple)):
                            replacement = ",".join(replacements[token])
                        elif isinstance(replacements[token], dict):
                            replacement = json.dumps(replacements[token])

                        if isinstance(config, str):
                            config = config.replace(token, str(replacement))
            return config

        for name, config in instance_data[component_name].items():
            if config and isinstance(config, dict):
                collection = config.pop('_foreach', None)

                if collection:
                    collection = self.command.options.interpolate(collection)

                    if isinstance(collection, (list, tuple)):
                        for item in collection:
                            replacements = get_replacements(item, {})
                            new_name = self.command.options.interpolate(substitute_config(name, replacements))
                            instance_map[new_name] = substitute_config(config, replacements)

                    elif isinstance(collection, dict):
                        for key, item in collection.items():
                            replacements = get_replacements(item, {
                                "<<dict_key>>": key
                            })
                            new_name = self.command.options.interpolate(substitute_config(name, replacements))
                            instance_map[new_name] = substitute_config(config, replacements)
                    else:
                        self.command.error("Component instance expansions must be lists or dictionaries: {}".format(collection))
                else:
                    instance_map[name] = config
            else:
                instance_map[name] = config

        for name, config in instance_map.items():
            if data is None:
                self.data[component_name][name] = config
            else:
                data[component_name][name] = config

        return instance_map

    def order_instances(self, configs, keep_requires = False):
        for name, value in configs.items():
            if isinstance(value, dict) and '_requires' in value and value['_requires'] is not None:
                value['_requires'] = self.command.options.interpolate(value['_requires'])

        return prioritize(configs, keep_requires = keep_requires, requires_field = '_requires')


    def include(self, component, force = False, check_data = True):
        if component == 'profile' and 'profile' in self.data:
            return True

        if not force and self.components and component not in self.components:
            return False

        if check_data and component not in self.data:
            return False
        return True

    def include_inner(self, component, force = False):
        return self.include(component,
            force = force,
            check_data = False
        )

    def include_instance(self, name, config):
        if isinstance(config, dict):
            when = config.pop('_when', None)
            when_not = config.pop('_when_not', None)
            when_in = config.pop('_when_in', None)
            when_not_in = config.pop('_when_not_in', None)
            when_type = config.pop('_when_type', 'AND').upper()

            if when is not None:
                result = True if when_type == 'AND' else False
                for variable in ensure_list(when):
                    value = format_value('bool', self.command.options.interpolate(variable))
                    if when_type == 'AND':
                        if not value:
                            return False
                    else:
                        if value:
                            result = True
                return result

            if when_not is not None:
                result = True if when_type == 'AND' else False
                for variable in ensure_list(when_not):
                    value = format_value('bool', self.command.options.interpolate(variable))
                    if when_type == 'AND':
                        if value:
                            return False
                    else:
                        if not value:
                            result = True
                return result

            if when_in is not None:
                value = self.command.options.interpolate(when_in)
                return name in ensure_list(value)

            if when_not_in is not None:
                value = self.command.options.interpolate(when_not_in)
                return name not in ensure_list(value)

        return True


    def get_variables(self, instance, variables = None):
        if not variables:
            variables = {}

        system_fields = [ x.name for x in instance.facade.system_field_instances ]

        if getattr(instance, 'config', None) and isinstance(instance.config, dict):
            for name, value in instance.config.items():
                variables[name] = value

        for field in instance.facade.fields:
            value = getattr(instance, field)

            if not isinstance(value, BaseModel) and field[0] != '_' and field not in system_fields:
                variables[field] = value

        return clean_dict(variables)


    def get_instances(self, facade_name, excludes = None):
        if not excludes:
            excludes = []

        facade_index = self.manager.index.get_facade_index()
        excludes = ensure_list(excludes)
        instances = []
        for instance in self.command.get_instances(facade_index[facade_name]):
            if not excludes or instance.name not in excludes:
                instances.append(instance)
        return instances

    def get_module(self, name):
        facade = self.command.facade(self.command._module)
        return self.command.get_instance(facade, name, required = False)


    def get_info(self, name, config, remove = True):
        if remove:
            value = config.pop(name, None)
        else:
            value = config.get(name, None)
        return value

    def pop_info(self, name, config):
        return self.get_info(name, config, True)

    def get_value(self, name, config, remove = False):
        value = self.get_info(name, config, remove)
        if value is not None:
            value = self.command.options.interpolate(value)
        return value

    def pop_value(self, name, config):
        return self.get_value(name, config, True)

    def get_values(self, name, config, remove = False):
        value = self.get_value(name, config, remove)
        return ensure_list(value) if value is not None else []

    def pop_values(self, name, config):
        return self.get_values(name, config, True)


    def interpolate(self, config, replacements = None):
        if not replacements:
            replacements = {}

        def _interpolate(data):
            if isinstance(data, dict):
                for key, value in data.items():
                    data[key] = _interpolate(value)
            elif isinstance(data, (list, tuple)):
                for index, value in enumerate(data):
                    data[index] = _interpolate(value)
            elif isinstance(data, str):
                data = re.sub(r"([\{\}])", r"\1\1", data)
                data = re.sub(r"\<([a-z][\_\-a-z0-9]+)\>", r"{\1}", data)
                data = data.format(**replacements)
            return data

        if replacements:
            return _interpolate(copy.deepcopy(config))
        return config
