from django.conf import settings

from data.base import BaseModel
from systems.command.options import AppOptions
from systems.command.parsers.config import ConfigParser
from utility.data import ensure_list, clean_dict, deep_merge, format_value

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


    def run(self, name, config):
        # Override in subclass
        pass

    def describe(self, instance):
        # Override in subclass
        return None

    def scope(self, instance):
        # Override in subclass
        return {}

    def variables(self, instance):
        # Override in subclass
        return {}

    def destroy(self, name, config):
        # Override in subclass
        pass


    def get_names(self, relation):
        return [ x.name for x in relation.all() ]

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
        self.exporting = False


    def initialize(self, config, components, display_only):
        self.components = components

        self.load_parents()
        self.data = self.get_schema(config)

        if display_only:
            self.display_schema()
            return False
        return True


    def display_schema(self):
        data = self.command.options.interpolate(
            self.data,
            ('config', 'state', 'token')
        )
        for config in self.command.get_instances(self.command._config):
            if config.name in data['config']:
                data['config'][config.name] = config.value

        self.command.data("> profile", self.name)
        self.command.data("> module", self.module.instance.name)
        self.command.info('')

        self.command.info(yaml.dump(
            { 'config': data['config'] },
            Dumper = noalias_dumper
        ))
        component_map = self.manager.load_components(self)
        for priority, components in sorted(component_map.items()):
            for component in components:
                if self.include(component.name):
                    self.command.info(yaml.dump(
                        { component.name: data[component.name] },
                        Dumper = noalias_dumper
                    ))
        if self.include('profile'):
            component = self.manager.load_component(self, 'profile')
            for profile, config in self.data['profile'].items():
                component.run(profile, config, True)


    def run(self, components = None, config = None, display_only = False, plan = False):
        if not components:
            components = []
        if not config:
            config = {}

        self.command.data("Running profile:", "{}:{}".format(self.module.instance.name, self.name))

        if self.initialize(config, components, display_only):
            component_map = self.manager.load_components(self)
            for priority, component_list in sorted(component_map.items()):
                def run_component(component):
                    component.test = plan

                    def component_process(name):
                        instance_config = self.data[component.name][name]
                        if self.include_instance(name, instance_config):
                            if isinstance(instance_config, dict):
                                instance_config.pop('keep', None)

                            name = self.command.options.interpolate(name)
                            component.run(name, instance_config)

                    if self.include(component.name) and component.name not in ('destroy', 'pre_destroy', 'post_destroy'):
                        instance_map = self.order_instances(self.data[component.name])
                        for priority, names in sorted(instance_map.items()):
                            self.command.run_list(names, component_process)

                self.command.run_list(component_list, run_component)
                if priority == 0:
                    self.command.options.initialize(True)


    def export(self, components = None):
        if not components:
            components = []

        self.components = ensure_list(components)
        self.exporting = True

        if not self.components or 'config' in self.components:
            self.data['config_store'] = {}
            for instance in self.get_instances('config'):
                self.data['config_store'][instance.name] = instance.value

        def process(component):
            if not self.components or component.name in self.components:
                if component.name not in ('config_store', 'run', 'pre_run', 'post_run', 'destroy', 'pre_destroy', 'post_destroy', 'profile'):
                    self.data[component.name] = {}
                    for instance in self.get_instances(component.name):
                        scope = component.scope(instance)
                        index_name = []
                        for variable, value in scope.items():
                            index_name.append(value)
                        index_name.append(instance.name)

                        data = component.describe(instance)
                        if data is None:
                            variables = { **scope, **component.variables(instance) }
                            data = self.get_variables(instance, variables)

                        self.data[component.name]["-".join(index_name)] = data

        component_map = self.manager.load_components(self)
        for priority, component_list in sorted(component_map.items()):
            self.command.run_list(component_list, process)

        return copy.deepcopy(self.data)


    def destroy(self, components = None, config = None, display_only = False):
        if not components:
            components = []
        if not config:
            config = {}

        self.command.data("Destroying profile:", "{}:{}".format(self.module.instance.name, self.name))

        if self.initialize(config, components, display_only):
            component_map = self.manager.load_components(self)

            for priority, component_list in sorted(component_map.items(), reverse = True):
                def run_component(component):
                    def component_process(name):
                        instance_config = self.data[component.name][name]
                        if self.include_instance(name, instance_config):
                            if not isinstance(instance_config, dict) or not instance_config.pop('keep', False):
                                name = self.command.options.interpolate(name)
                                component.destroy(name, instance_config)

                    if self.include(component.name) and component.name not in ('run', 'pre_run', 'post_run'):
                        instance_map = self.order_instances(self.data[component.name])
                        for priority, names in sorted(instance_map.items(), reverse = True):
                            self.command.run_list(names, component_process)

                self.command.run_list(component_list, run_component)


    def load_parents(self):
        self.parents = []
        if 'parents' in self.data:
            parents = self.data.pop('parents')
            for parent in ensure_list(parents):
                module = self.module.instance

                if isinstance(parent, str):
                    profile_name = parent
                else:
                    profile_name = parent['profile']
                    if 'module' in parent and parent['module'] != 'self':
                        module = self.get_module(parent['module'])

                profile = module.provider.get_profile(profile_name)
                profile.load_parents()
                self.parents.append(profile)

    def get_parents(self):
        parents = []
        for profile in self.parents:
            parents.extend(profile.get_parents())
            parents.append(profile)
        return parents


    def get_schema(self, config):
        schema = {}

        for profile in self.parents:
            profile_schema = profile.get_schema(config)
            profile_schema['config'] = self.interpolate_config(profile_schema.get('config', {}))
            self.merge_schema(schema, profile_schema)

        self.data['config'] = self.interpolate_config(
            deep_merge(self.data.get('config', {}), config)
        )
        self.merge_schema(schema, self.data)

        for component in ['run', 'pre_run', 'post_run', 'destroy', 'pre_destroy', 'post_destroy', 'profile']:
            if component in schema:
                for name, component_config in schema[component].items():
                    if 'module' not in component_config:
                        component_config['module'] = self.module.instance.name
        return schema

    def merge_schema(self, schema, data):
        for key, value in data.items():
            if isinstance(value, dict):
                schema.setdefault(key, {})
                self.merge_schema(schema[key], value)
            else:
                schema[key] = value


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

    def interpolate_config(self, config):
        for name, value in config.items():
            config[name] = self.command.options.interpolate(value)
            ConfigParser.runtime_variables[name] = config[name]
        return config


    def order_instances(self, configs):
        instance_map = {}
        priorities = {}
        dependents = {}

        for name, config in configs.items():
            priorities[name] = 0
            if config is not None and isinstance(config, dict):
                requires = self.pop_values('requires', config)
                if requires:
                    dependents[name] = requires

        while dependents:
            for name in list(dependents.keys()):
                remove = True
                for require in dependents[name]:
                    if require in priorities:
                        if name not in priorities:
                            priorities[name] = 0
                        priorities[name] = max(priorities[name], priorities[require] + 1)
                    else:
                        remove = False
                if remove:
                    dependents.pop(name)

        for name, priority in priorities.items():
            if priority not in instance_map:
                instance_map[priority] = []
            instance_map[priority].append(name)

        return instance_map


    def include(self, component, force = False, check_data = True):
        if self.exporting:
            return True

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
            when = config.pop('when', None)
            when_not = config.pop('when_not', None)
            when_in = config.pop('when_in', None)
            when_not_in = config.pop('when_not_in', None)

            if when is not None:
                for variable in ensure_list(when):
                    value = self.command.options.interpolate(variable)
                    if not format_value('bool', value):
                        return False
                return True

            if when_not is not None:
                for variable in ensure_list(when_not):
                    value = self.command.options.interpolate(variable)
                    if format_value('bool', value):
                        return False
                return True

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


    def get_instances(self, type, excludes = None):
        if not excludes:
            excludes = []

        facade_index = self.manager.get_facade_index()
        excludes = ensure_list(excludes)
        instances = []
        for instance in self.command.get_instances(facade_index[type]):
            if not excludes or instance.name not in excludes:
                instances.append(instance)
        return instances

    def get_module(self, name):
        facade = self.command.facade(self.command._module)
        return self.command.get_instance(facade, name, required = False)
