from plugins import base
from systems.models.base import BaseModel
from utility import data

import datetime
import copy


class DataProviderState(object):

    def __init__(self, data):
        if isinstance(data, DataProviderState):
            self.state = data.export()
        else:
            self.state = copy.deepcopy(data) if isinstance(data, dict) else {}

    def export(self):
        return copy.deepcopy(self.state)

    def get_value(self, data, *keys):
        if isinstance(data, (dict, list, tuple)):
            name = keys[0]
            keys = keys[1:] if len(keys) > 1 else []
            value = data.get(name, None)

            if not len(keys):
                return value
            else:
                return self.get_value(value, *keys)

        return None

    def get(self, *keys):
        return self.get_value(self.state, *keys)

    @property
    def variables(self):
        return {}


class BasePlugin(base.BasePlugin):

    @classmethod
    def generate(cls, plugin, generator):
        super().generate(plugin, generator)

        def facade(self):
            return self.command.facade(generator.spec['data'])

        def store_lock_id(self):
            return generator.spec['store_lock']

        if generator.spec.get('data', None):
            plugin.facade = property(facade)

        if generator.spec.get('store_lock', None):
            plugin.store_lock_id = store_lock_id


    def __init__(self, type, name, command, instance = None):
        super().__init__(type, name, command)
        self.instance = instance

    def check_instance(self, op):
        if not self.instance:
            self.command.error("Provider {} operation '{}' requires a valid model instance given to provider on initialization".format(self.name, op))
        return self.instance


    @property
    def facade(self):
        # Override in subclass
        return None


    def provider_state(self):
        return DataProviderState


    def get(self, name, required = True):
        return self.command.get_instance(self.facade, name, required = required)

    def get_variables(self, instance, standardize = False, recurse = True, parents = None):
        variables = {}

        if parents is None:
            parents = []

        instance.initialize(self.command)

        if getattr(instance, 'config', None) and isinstance(instance.config, dict):
            for name, value in instance.config.items():
                variables[name] = value

        if getattr(instance, 'secrets', None) and isinstance(instance.secrets, dict):
            for name, value in instance.secrets.items():
                variables[name] = value

        if getattr(instance, 'variables', None) and isinstance(instance.variables, dict):
            for name, value in instance.variables.items():
                variables[name] = value

        for field_name in instance.facade.fields:
            value = getattr(instance, field_name)

            if field_name[0] != '_' and field_name not in ('config', 'secrets', 'variables'):
                variables[field_name] = value

            if value and isinstance(value, datetime.datetime):
                variables[field_name] = value.strftime("%Y-%m-%d %H:%M:%S %Z")

        for field_name, value in variables.items():
            if isinstance(value, BaseModel):
                if recurse:
                    variables[field_name] = self.get_variables(value, standardize)
                else:
                    variables[field_name] = getattr(value, value.facade.key())

            elif isinstance(value, (list, tuple)):
                model_list = False
                for index, item in enumerate(value):
                    if isinstance(item, BaseModel):
                        model_list = True
                        if recurse:
                            value[index] = self.get_variables(item, standardize, False)
                        else:
                            value[index] = getattr(item, item.facade.key())

                if standardize and model_list:
                    self.standardize_list_variables(value)

        if instance.get_id() not in parents:
            parents.append(instance.get_id())

            for variable, elements in self.get_related_variables(instance, standardize, parents).items():
                if variable not in variables:
                    if standardize and isinstance(elements, (list, tuple)):
                        self.standardize_list_variables(elements)
                    variables[variable] = elements

        return variables

    def get_related_variables(self, instance, standardize = False, parents = None):
        relation_values = self.command.get_relations(instance.facade)
        variables = {}

        if parents is None:
            parents = []

        for field_name, relation_info in instance.facade.get_extra_relations().items():
            variables[field_name] = []
            related_instances = self.get_instance_values(
                relation_values.get(field_name, None),
                getattr(instance, field_name),
                self.command.facade(relation_info['model'].facade)
            )
            for related_instance in related_instances:
                variables[field_name].append(self.get_variables(related_instance, standardize, False, parents))

        return variables


    def get_instance_values(self, names, relations, facade):
        instances = []

        if names:
            self.command.set_scope(facade)
            for instance in self.command.get_instances(facade, names = names):
                instances.append(instance)
        elif relations and getattr(relations, 'all', None):
            for instance in relations.all():
                instances.append(instance)
        elif isinstance(relations, BaseModel):
            instances.append(relations)

        return instances


    def standardize_list_variables(self, elements):
        element_values = {}
        mixed_values = []

        for item in elements:
            for key in item.keys():
                element_values.setdefault(key, [])
                element_values[key].append(type(item[key]))

        for key, types in element_values.items():
            if len(set(types)) > 1:
                mixed_values.append(key)

        for index, item in enumerate(elements):
            for key in mixed_values:
                item.pop(key)


    def initialize_instances(self):
        # Override in subclass
        pass

    def preprocess_fields(self, fields, instance = None):
        # Override in subclass
        return fields

    def initialize_instance(self, instance, created):
        # Override in subclass
        pass

    def prepare_instance(self, instance, created):
        # Override in subclass
        pass

    def store_related(self, instance, created, test):
        # Override in subclass
        pass

    def finalize_instance(self, instance):
        # Override in subclass
        pass


    def generate_name(self, prefix, state_variable):
        name_index = int(self.command.get_state(state_variable, 0)) + 1
        self.command.set_state(state_variable, name_index)
        return "{}{}".format(prefix, name_index)


    def _init_config(self, fields, create = True):
        self.create_op = create
        self.config = copy.copy(fields)
        self.provider_config()
        self.validate()


    def store_lock_id(self):
        # Override in subclass
        return None

    def store(self, key, values, relation_key = True, quiet = False):
        instance = None
        model_fields = {}
        provider_fields = {}
        provider_secrets = {}
        created = False

        # Initialize instance
        scope, fields, relations, reverse = self.facade.split_field_values(values)
        secret_fields = self.get_secret_fields()

        self.facade.set_scope(scope)

        if key is not None:
            if isinstance(key, BaseModel):
                instance = key
            else:
                instance = self.facade.retrieve(key)

        if not instance:
            fields = { **self.config, **self.secrets, **fields }

        fields['provider_type'] = self.name

        for field, value in fields.items():
            if field in self.facade.fields:
                if fields[field] is not None:
                    model_fields[field] = fields[field]
            elif field in secret_fields:
                provider_secrets[field] = fields[field]
            else:
                provider_fields[field] = fields[field]

        if not instance:
            instance = self.facade.create(key, model_fields)
            created = True
        else:
            for field, value in model_fields.items():
                setattr(instance, field, value)

        instance.config = { **instance.config, **provider_fields }
        instance.secrets = { **instance.secrets, **provider_secrets }

        self.instance = instance

        def process():
            # Save instance
            self.initialize_instance(instance, created)

            if self.test:
                self.store_related(instance, created, True)
                self.command.success("Test complete")
            else:
                try:
                    if getattr(instance, 'variables', None) is not None:
                        instance.variables = self._collect_variables(instance, instance.variables)

                    self.prepare_instance(instance, created)
                    instance.save()

                except Exception as e:
                    if created:
                        if not quiet:
                            self.command.info("Save failed, now reverting any associated resources...")
                        self.finalize_instance(instance)
                    raise e

                self.facade.save_relations(
                    instance,
                    relations,
                    relation_key = relation_key,
                    command = self.command
                )
                self.store_related(instance, created, False)
                if not quiet:
                    self.command.success("Successfully saved {} '{}'".format(self.facade.name, getattr(instance, instance.facade.key())))

        self.run_exclusive(self.store_lock_id(), process)
        return instance


    def create(self, key, values = None, relation_key = True, quiet = False):
        if not values:
            values = {}

        if self.command.check_available(self.facade, key):
            values = self.preprocess_fields(data.normalize_dict(values))
            self._init_config(values, True)
            return self.store(key, values, relation_key = relation_key, quiet = quiet)
        else:
            self.command.error("Instance '{}' already exists".format(key))

    def update(self, values = None, relation_key = True, quiet = False):
        if not values:
            values = {}

        instance = self.check_instance('instance update')
        values = self.preprocess_fields(data.normalize_dict(values), instance)

        self._init_config(values, False)
        return self.store(instance, values, relation_key = relation_key, quiet = quiet)


    def delete_lock_id(self):
        # Override in subclass
        return None

    def delete(self, force = False):
        instance = self.check_instance('instance delete')
        instance_id = getattr(instance, instance.facade.pk)
        instance_key = getattr(instance, instance.facade.key())

        def process():
            if self.facade.keep(instance_key):
                self.command.error("Removal of {} {} is restricted (has dependencies)".format(self.facade.name, instance_key))

            for child in self.facade.get_children():
                sub_facade = child['facade']
                field = child['field']

                for sub_instance in sub_facade.filter(**{ "{}_id".format(field.name): instance_id }):
                    if getattr(sub_facade, 'provider_name', None):
                        sub_instance.initialize(self.command)
                        sub_instance.provider.delete(force)
                    else:
                        sub_facade.clear(**{ sub_facade.pk: getattr(sub_instance, sub_facade.pk) })
            try:
                self.finalize_instance(instance)
            except Exception as e:
                if not force:
                    raise e

            if self.facade.delete(instance_key):
                self.command.success("Successfully deleted {} '{}'".format(self.facade.name, instance_key))
            else:
                self.command.error("{} '{}' deletion failed".format(self.facade.name.title(), instance_key))

        self.run_exclusive(self.delete_lock_id(), process)


    def _collect_variables(self, instance, variables = None):
        collected_variables = {}
        if not variables:
            variables = {}

        for variable, value in variables.items():
            collected_variables[variable] = value

        return collected_variables
