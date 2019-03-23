from django.conf import settings

from systems.models.base import AppModel
from systems.command.base import AppOptions
from utility.data import ensure_list, clean_dict, format_value

import copy
import json


class BaseProvisioner(object):

    def __init__(self, name, profile):
        self.name = name
        self.profile = profile
        self.command = profile.command
        self.manager = self.command.manager

    def priority(self):
        return 10

    def ensure(self, name, config):
        # Override in subclass
        pass

    def describe(self, instance):
        # Override in subclass
        return {}

    def destroy(self, name, config):
        # Override in subclass
        pass


class CommandProfile(object):

    def __init__(self, module, data = {}):
        self.module = module
        self.command = module.command
        self.manager = self.command.manager
        self.data = data
        self.components = []
        self.config = AppOptions(type(self.command)())
        self.exporting = False


    def initialize(self, components):
        self.components = components

        self.load_parents()
        self.data = self.get_schema()

        self.ensure_config()
        self.config.init_variables()


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


    def provision(self, components = []):
        self.initialize(components)

        provisioner_map = self.manager.load_provisioners(self)
        for priority, provisioners in sorted(provisioner_map.items()):
            def run_provisioner(provisioner):
                def process(name):
                    config = self.data[provisioner.name][name]
                    if self.include_instance(name, config):
                        provisioner.ensure(name, config)

                if self.include(provisioner.name):
                    self.command.run_list(self.data[provisioner.name].keys(), process)

            self.command.run_list(provisioners, run_provisioner)


    def export(self, components = []):
        self.components = components
        self.exporting = True

        def process(self, provisioner):
            self.data[provisioner.name] = {}
            for instance in self.get_instances(provisioner.name, required = False):
                variables = provisioner.describe(instance)
                index_name = []
                for variable, value in variables.items():
                    if variable != 'provider':
                        index_name.append(value)
                index_name.append(instance.name)

                self.data[provisioner.name]["-".join(index_name)] = self.get_variables(
                    instance,
                    variables
                )

        provisioner_map = self.manager.load_provisioners(self)
        for priority, provisioners in sorted(provisioner_map.items()):
            self.command.run_list(provisioners, process)

        return copy.deepcopy(self.data)


    def destroy(self, components = []):
        self.initialize(components)

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


    def include(self, component, force = False):
        if self.exporting:
            return True

        if not force and self.components and component not in self.components:
            return False

        if component not in self.data:
            return False
        return True

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
        if getattr(instance, 'config', None) and isinstance(instance.config, dict):
            config = instance.config.get(namespace, {}) if namespace else instance.config
            for name, value in config.items():
                variables[name] = value

        for field in instance.facade.fields:
            value = getattr(instance, field)

            if not isinstance(value, AppModel) and field[0] != '_' and field not in (
                'id',
                'name',
                'type',
                'config',
                'variables',
                'state_config',
                'created',
                'updated'
            ):
                variables[field] = value

        return clean_dict(variables)


    def get_instance(self, type, name):
        facade = getattr(self.command, "_{}".format(type))
        return facade.retrieve(name)

    def get_instances(self, type, excludes = []):
        excludes = ensure_list(excludes)
        facade = getattr(self.command, "_{}".format(type))
        instances = []
        for instance in self.command.get_instances(facade):
            if not excludes or instance.name not in excludes:
                instances.append(instance)
        return instances

    def get_module(self, name):
        facade = self.command.facade(self.command._module)
        return self.command.get_instance(facade, name, required = False)
