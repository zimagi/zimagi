from django.conf import settings

from systems.models.base import AppModel
from systems.command.base import AppOptions
from utility.data import ensure_list, clean_dict, format_value

import copy


class ProjectProfile(object):

    def __init__(self, project, data = {}):
        self.project = project
        self.command = project.command
        self.data = data
        self.components = []
        self.config = AppOptions(type(self.command)())
        self.exporting = False

    def _init_update(self, components):
        self._ensure('project', force = True)
        self.load_parents(components)
        self._ensure('config', force = True)

        self.data = self.get_schema()
        self.components = components
        self.config.init_variables()


    def _ensure(self, type, force = False):
        def process(name):
            config = self.data[type][name]
            if force or self.include_instance(name, config):
                method = "ensure_{}".format(type)
                getattr(self, method)(name, config)

        if self.include(type, force):
            self.command.run_list(self.data[type].keys(), process)

    def _export(self, type, excludes = [], use_config = True, namespace = None, field = None):
        describe_method = "describe_{}".format(type)
        index = {}
        for instance in self.get_instances(type, excludes):
            if describe_method and callable(describe_method):
                variables = getattr(self, describe_method)(instance)
            else:
                variables = {}

            index_name = []
            for variable, value in variables.items():
                if variable != 'provider':
                    index_name.append(value)
            index_name.append(instance.name)

            if field:
                value = getattr(instance, field, None)
            else:
                value = self.get_variables(instance, variables,
                    use_config = use_config,
                    namespace = namespace
                )
            index["-".join(index_name)] = value

        self.data[type] = index

    def _clear(self, type, force = False, excludes = []):
        excludes = ensure_list(excludes)

        def process(name):
            if not excludes or name not in excludes:
                config = self.data[type][name]
                if force or self.include_instance(name, config):
                    method = "destroy_{}".format(type)
                    getattr(self, method)(name, config)

        if self.include(type):
            self.command.run_list(self.data[type].keys(), process)


    def provision(self, components = []):
        self._init_update(components)

        #self._ensure('network')
        #self._ensure('subnet')
        #self._ensure('firewall')

    def export(self, components = []):
        self.components = components
        self.exporting = True

        self._export('config', field = 'value')
        self._export('project', excludes = settings.CORE_PROJECT)
        #self._export('network')
        #self._export('subnet')
        #self._export('firewall')

        return copy.deepcopy(self.data)

    def destroy(self, components = []):
        self._init_update(components)

        #self._clear('network')
        self._clear('project', force = True, excludes = settings.CORE_PROJECT)
        self._clear('config', force = True)


    def load_parents(self, components):
        self.parents = []
        if 'parents' in self.data:
            for parent in ensure_list(self.data['parents']):
                project = self.get_project(parent['project'])
                profile = project.provider.get_profile(parent['profile'])
                profile._init_update(components)
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


    def get_variables(self, instance, variables = {}, use_config = True, namespace = None):
        if use_config and getattr(instance, 'config', None) and isinstance(instance.config, dict):
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
