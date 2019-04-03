from django.conf import settings

from systems.models.base import AppModel
from systems.command.base import AppOptions
from utility.data import ensure_list, clean_dict, format_value

import re
import copy
import json
import yaml


class BaseProvisioner(object):

    def __init__(self, name, profile):
        self.name = name
        self.profile = profile
        self.command = profile.command
        self.manager = self.command.manager
        self.test = False

    def priority(self):
        return 10


    def ensure(self, name, config):
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

    def get_variables(self, instance, variables = {}):
        return self.profile.get_variables(instance, variables)


    def exec(self, command, **parameters):
        self.command.exec_local(command, parameters)

    def run_list(self, elements, processor):
        self.command.run_list(elements, processor)


class CommandProfile(object):

    def __init__(self, module, data = {}):
        self.module = module
        self.command = module.command
        self.manager = self.command.manager
        self.data = data
        self.components = []
        self.config = AppOptions(type(self.command)(
            self.command.name,
            self.command.parent_instance
        ))
        self.exporting = False


    def initialize(self, components, test):
        self.components = components

        self.load_parents()
        self.data = self.get_schema()

        if test:
            self.command.info(yaml.dump(self.data))
            return False

        self.ensure_config()
        self.config.init_variables()
        return True


    def ensure_config(self):
        provisioner = self.manager.load_config_provisioner(self)

        def process(name):
            provisioner.ensure(name, self.data['config'][name])

        if self.include('config', True):
            self.command.run_list(self.data['config'].keys(), process)

    def export_config(self):
        provisioner = self.manager.load_config_provisioner(self)

        self.data[provisioner.name] = {}
        for instance in self.get_instances(provisioner.name):
            self.data[provisioner.name][instance.name] = instance.value

    def destroy_config(self):
        provisioner = self.manager.load_config_provisioner(self)

        def process(name):
            provisioner.destroy(name, self.data['config'][name])

        if self.include('config', True):
            self.command.run_list(self.data['config'].keys(), process)


    def provision(self, components = [], test = False, plan = False):
        if self.initialize(components, test):
            provisioner_map = self.manager.load_provisioners(self)
            for priority, provisioners in sorted(provisioner_map.items()):
                def run_provisioner(provisioner):
                    provisioner.test = plan

                    def process(name):
                        config = self.data[provisioner.name][name]
                        if self.include_instance(name, config):
                            provisioner.ensure(name, config)

                    if self.include(provisioner.name):
                        self.command.run_list(self.data[provisioner.name].keys(), process)

                self.command.run_list(provisioners, run_provisioner)


    def export(self, components = []):
        self.components = ensure_list(components)
        self.exporting = True

        if not self.components or 'config' in self.components:
            self.export_config()

        def process(provisioner):
            if not self.components or provisioner.name in self.components:
                self.data[provisioner.name] = {}
                for instance in self.get_instances(provisioner.name):
                    scope = provisioner.scope(instance)
                    index_name = []
                    for variable, value in scope.items():
                        index_name.append(value)
                    index_name.append(instance.name)

                    data = provisioner.describe(instance)
                    if data is None:
                        variables = { **scope, **provisioner.variables(instance) }
                        data = self.get_variables(instance, variables)

                    self.data[provisioner.name]["-".join(index_name)] = data

        provisioner_map = self.manager.load_provisioners(self)
        for priority, provisioners in sorted(provisioner_map.items()):
            self.command.run_list(provisioners, process)

        return copy.deepcopy(self.data)


    def destroy(self, components = [], test = False):
        if self.initialize(components, test):
            config_provisioner = self.manager.load_config_provisioner(self)
            provisioner_map = self.manager.load_provisioners(self)

            for priority, provisioners in sorted(provisioner_map.items(), reverse = True):
                def run_provisioner(provisioner):
                    def provisioner_process(name):
                        config = self.data[provisioner.name][name]
                        if self.include_instance(name, config):
                            provisioner.destroy(name, config)

                    if self.include(provisioner.name):
                        self.command.run_list(self.data[provisioner.name].keys(), provisioner_process)

                self.command.run_list(provisioners, run_provisioner)

            self.destroy_config()


    def load_parents(self):
        self.parents = []
        if 'parents' in self.data:
            parents = self.data.pop('parents')
            for parent in ensure_list(parents):
                module = self.get_module(parent['module'])
                profile = module.provider.get_profile(parent['profile'])
                profile.load_parents()
                self.parents.append(profile)

    def get_parents(self):
        parents = []
        for profile in self.parents:
            parents.extend(profile.get_parents())
            parents.append(profile)
        return parents


    def get_schema(self):
        schema = {}
        for profile in self.parents:
            self.merge_schema(schema, profile.get_schema())
        self.merge_schema(schema, self.data)
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
            if isinstance(value, str):
                value = self.config.interpolate(value)
        return value

    def pop_value(self, name, config):
        return self.get_value(name, config, True)

    def get_values(self, name, config, remove = False):
        value = self.get_value(name, config, remove)
        return ensure_list(value) if value is not None else []

    def pop_values(self, name, config):
        return self.get_values(name, config, True)

    def interpolate(self, config, replacements = {}):
        data = {}
        tokens = {}
        for key, value in replacements.items():
            tokens[key] = "[{}]".format(value)

        if isinstance(config, dict) and tokens:
            for key, value in config.items():
                if isinstance(value, str):
                    value = re.sub(r"^(@[a-z][\_\-a-z0-9]+)\[([^\]]+)\]$", r"\1{\2}", value)
                    value = value.format(**tokens)

                data[key] = value
        return data


    def include(self, component, force = False, check_data = True):
        if self.exporting:
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
                value = self.config.interpolate(when)
                return format_value('bool', value)

            if when_not is not None:
                value = self.config.interpolate(when_not)
                return not format_value('bool', value)

            if when_in is not None:
                value = self.config.interpolate(when_in)
                return name in ensure_list(value)

            if when_not_in is not None:
                value = self.config.interpolate(when_not_in)
                return name not in ensure_list(value)

        return True


    def get_variables(self, instance, variables = {}, namespace = None):
        system_fields = [ x.name for x in instance.facade.system_field_instances ]

        if getattr(instance, 'config', None) and isinstance(instance.config, dict):
            config = instance.config.get(namespace, {}) if namespace else instance.config
            for name, value in config.items():
                variables[name] = value

        for field in instance.facade.fields:
            value = getattr(instance, field)

            if not isinstance(value, AppModel) and field[0] != '_' and field not in system_fields:
                variables[field] = value

        return clean_dict(variables)


    def get_instances(self, type, excludes = []):
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
