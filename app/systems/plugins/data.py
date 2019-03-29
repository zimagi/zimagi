from systems.models.base import AppModel
from utility import query, data
from .base import BasePluginProvider

import datetime
import copy
import re


class DataProviderState(object):

    def __init__(self, data):
        if isinstance(data, DataProviderState):
            self.state = data.export()
        else:
            self.state = data if isinstance(data, dict) else {}

    def export(self):
        return self.state

    def get_value(self, data, *keys):
        if isinstance(data, (dict, list, tuple)):
            name = keys[0]
            keys = keys[1:] if len(keys) > 1 else []

            if isinstance(data, dict):
                value = data.get(name, None)
            else:
                try:
                    value = data[name]
                except KeyError:
                    pass

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


class DataPluginProvider(BasePluginProvider):

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


    def get(self, name, namespace = None, required = True):
        instance = self.command.get_instance(self.facade, name, required = required)
        if getattr(instance, 'state_config', None):
            state = instance.state_config.get(namespace, {}) if namespace else instance.state_config
            state = self.provider_state()(state)
            if namespace:
                instance.state_config[namespace] = state
            else:
                instance.state_config = state

    def get_variables(self, instance, namespace = None):
        variables = {}

        if getattr(instance, 'config', None) and isinstance(instance.config, dict):
            config = instance.config.get(namespace, {}) if namespace else instance.config
            for name, value in config.items():
                variables[name] = value

        if getattr(instance, 'variables', None) and isinstance(instance.variables, dict):
            config = instance.variables.get(namespace, {}) if namespace else instance.variables
            for name, value in config.items():
                variables[name] = value

        for field in instance.facade.fields:
            value = getattr(instance, field)

            if field[0] != '_' and field not in ('config', 'variables', 'state_config'):
                variables[field] = value

            if value and isinstance(value, datetime.datetime):
                variables[field] = value.strftime("%Y-%m-%d %H:%M:%S %Z")

        for field, value in variables.items():
            if isinstance(value, AppModel):
                variables[field] = self.get_variables(value)

        return variables


    def initialize_instances(self):
        # Override in subclass
        pass

    def initialize_instance(self, instance, created):
        # Override in subclass
        pass

    def prepare_instance(self, instance, created):
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


    def store(self, reference, fields):
        model_fields = {}
        provider_fields = {}
        created = False

        if isinstance(reference, AppModel):
            instance = reference
        else:
            instance = self.facade.retrieve(reference)

        if not instance:
            fields = self.config

        fields['type'] = self.name

        for field, value in fields.items():
            if field in self.facade.fields:
                if fields[field] is not None:
                    model_fields[field] = fields[field]
            else:
                provider_fields[field] = fields[field]

        model_fields = data.normalize_dict(model_fields)
        if not instance:
            instance = self.facade.create(reference, **model_fields)
            created = True
        else:
            for field, value in model_fields.items():
                setattr(instance, field, value)

        provider_fields = data.normalize_dict(provider_fields)

        instance.config = {**instance.config, **provider_fields}
        self.initialize_instance(instance, created)

        if self.test:
            self.command.success("Test complete")
        else:
            try:
                if getattr(instance, 'variables', None) is not None:
                    instance.variables = self._collect_variables(instance, instance.variables)

                self.prepare_instance(instance, created)
                instance.save()

            except Exception as e:
                if created:
                    self.command.info("Save failed, now reverting any associated resources...")
                    self.finalize_instance(instance)
                raise e

            instance.save_related(self)
            self.command.success("Successfully saved {} {}".format(self.facade.name, instance.name))

        return instance


    def create(self, name, fields = {}):
        if self.command.check_available(self.facade, name):
            self._init_config(fields, True)
            return self.store(name, fields)
        else:
            self.command.error("Instance {} already exists".format(name))

    def update(self, fields = {}):
        instance = self.check_instance('instance update')

        self._init_config(fields, False)
        return self.store(instance, fields)

    def delete(self):
        instance = self.check_instance('instance delete')
        self.finalize_instance(instance)

        if self.facade.delete(instance.name):
            self.command.success("Successfully deleted {} {}".format(self.facade.name, instance.name))
        else:
            self.command.error("{} {} deletion failed".format(self.facade.name.title(), instance.name))


    def add_related(self, instance, relation, facade, names, **fields):
        for field in fields.keys():
            if field not in facade.fields:
                self.command.error("Given field {} is not in {}".format(field, facade.name))

        queryset = query.get_queryset(instance, relation)
        instance_name = type(instance).__name__.lower()

        if queryset:
            for name in names:
                sub_instance = self.command.get_instance(facade, name, required = False)

                if not sub_instance:
                    provider_type = fields.pop('type', 'internal')
                    provider = self.command.get_provider(facade.provider_name, provider_type)
                    sub_instance = provider.create(name, fields)
                elif fields:
                    sub_instance.provider.update(name, fields)

                if sub_instance:
                    try:
                        with facade.thread_lock:
                            queryset.add(sub_instance)
                    except Exception as e:
                        self.command.error("{} add failed: {}".format(facade.name.title(), str(e)))

                    self.command.success("Successfully added {} {} to {} {}".format(sub_instance.facade.name, name, instance.facade.name, str(instance)))
                else:
                    self.command.error("{} {} creation failed".format(facade.name.title(), name))
        else:
            self.command.error("There is no relation {} on {} class".format(relation, instance_name))

    def remove_related(self, instance, relation, facade, names):
        queryset = query.get_queryset(instance, relation)
        instance_name = type(instance).__name__.lower()

        key = getattr(instance, instance.facade.key())
        keep_index = instance.facade._keep_relations().get(relation, {})
        keep = data.ensure_list(keep_index.get(key, []))

        if queryset:
            for name in names:
                if name not in keep:
                    sub_instance = facade.retrieve(name)

                    if sub_instance:
                        try:
                            with facade.thread_lock:
                                queryset.remove(sub_instance)
                        except Exception as e:
                            self.command.error("{} remove failed: {}".format(facade.name.title(), str(e)))

                        self.command.success("Successfully removed {} {} from {} {}".format(sub_instance.facade.name, name, instance.facade.name, key))
                    else:
                        self.command.warning("{} {} does not exist".format(facade.name.title(), name))
                else:
                    self.command.error("{} {} removal from {} is restricted".format(facade.name.title(), name, key))
        else:
            self.command.error("There is no relation {} on {} class".format(relation, instance_name))

    def update_related(self, instance, relation, facade, names, **fields):
        if names is None:
            queryset = query.get_queryset(instance, relation)
            if queryset:
                queryset.clear()
            else:
                self.command.error("Instance {} relation {} is not a valid queryset".format(instance.name, relation))
        else:
            add_names, remove_names = self._parse_add_remove_names(names)

            if add_names:
                self.add_related(
                    instance, relation,
                    facade,
                    add_names,
                    **fields
                )

            if remove_names:
                self.remove_related(
                    instance, relation,
                    facade,
                    remove_names
                )

    def set_related(self, instance, relation, facade, value, **fields):
        if value is None:
            setattr(instance, relation, None)
        else:
            if isinstance(value, str):
                if re.match(r'(none|null)', value, re.IGNORECASE):
                    setattr(instance, relation, None)
                else:
                    sub_instance = self.command.get_instance(facade, value, required = False)

                    if not sub_instance:
                        provider_type = fields.pop('type', 'internal')
                        provider = self.command.get_provider(facade.provider_name, provider_type)
                        sub_instance = provider.create(name, fields)
                    elif fields:
                        sub_instance.provider.update(name, fields)

                    if sub_instance:
                        setattr(instance, relation, sub_instance)
                        self.command.success("Successfully added {} {} to {} {}".format(sub_instance.facade.name, value, instance.facade.name, str(instance)))
                    else:
                        self.command.error("{} {} creation failed".format(facade.name.title(), value))
            else:
                setattr(instance, relation, value)

        instance.save()


    def _parse_add_remove_names(self, names):
        add_names = []
        remove_names = []

        if names:
            for name in names:
                name = re.sub(r'\s+', '', name)
                matches = re.search(r'^~(.*)$', name)
                if matches:
                    remove_names.append(matches.group(1))
                else:
                    name = name[1:] if name[0] == '+' else name
                    add_names.append(name)

        return (add_names, remove_names)


    def _collect_variables(self, instance, variables = {}, namespace = None):
        if getattr(instance, 'state_config', None) is not None:
            state = instance.state_config.get(namespace, {}) if namespace else instance.state_config
            state = self.provider_state()(state)
            for variable, value in state.variables.items():
                variables[variable] = value
        return variables


    def _get_field_info(self, fields):
        field_names = []
        field_labels = []

        for field in fields:
            if isinstance(field, (list, tuple)):
                field_names.append(field[0])
                field_labels.append(field[1])
            else:
                field_names.append(field)
                field_labels.append(field)

        return (field_names, field_labels)

    def _get_field_labels(self, processed_fields, existing_fields, labels):
        for index, value in enumerate(processed_fields):
            try:
                existing_index = existing_fields.index(value)
                processed_fields[index] = labels[existing_index]
            except Exception as e:
                pass

        return processed_fields
