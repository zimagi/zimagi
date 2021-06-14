from django.conf import settings

from systems.plugins.index import BasePlugin
from plugins.parser.config import ConfigTemplate
from utility.data import ensure_list

import threading
import importlib
import glob
import re
import copy
import logging
import yaml


logger = logging.getLogger(__name__)


for directory in settings.MANAGER.index.get_module_dirs('plugins/calculation/functions'):
    for function_file in glob.glob("{}/*.py".format(directory)):
        spec = importlib.util.spec_from_file_location("module.name", function_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        for function in dir(module):
            globals()[function] = getattr(module, function)


class SilentException(Exception):
    pass

class ProcessException(Exception):
    pass


class ParameterData(object):

    def __init__(self, data = None):
        self.parameters = {}
        if isinstance(data, dict):
            self.parameters = data

    def __getattr__(self, name):
        return self.parameters.get(name, None)

    def __str__(self):
        message = ""
        for name, value in self.parameters.items():
            message = message + " << {} >> {}\n".format(name, value)
        return message


class BaseProvider(BasePlugin('calculation')):

    thread_lock = threading.Lock()


    def __init__(self, type, name, command, id, config):
        super().__init__(type, name, command)
        self.id = id
        self.config = config


    def check(self, *args):
        for arg in args:
            if arg is None:
                return False
        return True

    def calc(self, params):
        # Override in subclass
        return None


    def set_null(self):
        raise SilentException()

    def abort(self, message = ''):
        raise ProcessException(message)


    def process(self, reset):
        facade = self.command.facade(self.field_data, False)
        success = True
        for record in self.load_items(facade, reset):
            if not self.process_item(facade, record):
                success = False
        if not success:
            self.abort("Calculations failed with errors")


    def load_items(self, facade, reset):
        filters = self._interpolate_values(self.field_filters)
        if not reset and not self.field_record:
            filters["{}__isnull".format(self.field_field)] = True

        return facade.values(*self._collect_fields(facade), **filters)

    def process_item(self, facade, record):
        key = record[facade.key()]
        params = ParameterData(self._collect_parameter_values(record))
        success = True

        try:
            value = self.calc(params)
        except SilentException:
            value = None
        except Exception as e:
            self.command.error("Error: {}:\n\n{}\n{}".format(e, yaml.dump(record, indent = 2), params), terminate = False)
            value = None
            success = False

        if self._validate_value(key, value, record):
            if not self.field_disable_save:
                if not self.field_record:
                    self._save_column(facade, value, record)

                elif value is not None:
                    data_type = self.field_record.get('_data', self.field_data)
                    self._save_row(self.command.facade(data_type, False), value, record)
        else:
            self.command.warning("Skipping {} {} value {}: {}".format(
                self.id,
                key,
                value,
                record
            ))
        return success


    def _get_parents(self, record):
        parents = {}
        if self.field_parents:
            for data_name, record_spec in self.field_parents.items():
                facade = self.command.facade(data_name, False)
                values = self._interpolate_values(record_spec, record)

                self._set_scope(facade, values)
                instance, created = facade.store(values[facade.key()], **values)
                parents[data_name] = getattr(instance, facade.pk)

        return parents

    def _set_scope(self, facade, values):
        scope = {}

        for field in facade.scope_fields:
            field_id = "{}_id".format(field)
            if field in values:
                scope[field] = values[field]
            elif field_id in values:
                scope[field_id] = values[field_id]

        facade.set_scope(scope)


    def _save_column(self, facade, value, record):
        instance = facade.retrieve_by_id(record[facade.pk])
        setattr(instance, self.field_field, value)
        instance.save()

    def _save_row(self, facade, value, record):
        record_spec = copy.deepcopy(self.field_record)
        record_spec[self.field_field] = value
        record_spec.pop('_data')

        for data_name, data_value in self._get_parents(record).items():
            record[data_name] = data_value

        values = self._interpolate_values(record_spec, record)
        self._set_scope(facade, values)
        facade.store(values[facade.key()], **values)


    def _collect_fields(self, facade):
        fields = {
            facade.pk: True,
            facade.key(): True,
            self.field_field: True
        }

        def add_fields(data):
            if data:
                for key, values in data.items():
                    for value in ensure_list(values):
                        if isinstance(value, str):
                            match = re.search(r'\@\{?([a-zA-Z0-9\_\-]+)\}?', value.strip())
                            if match:
                                for field in match.groups():
                                    fields[field] = True

        add_fields(self.field_filters)

        if self.field_parents:
            for data_name, record in self.field_parents.items():
                add_fields(record)

        for name, info in self.field_params.items():
            if isinstance(info, str):
                fields[info] = True
            else:
                add_fields(info.get('filters', {}))

                for field in ensure_list(info.get('order', [])):
                    fields[re.sub(r'^[~-]', '', field)] = True

        if self.field_extra_fields:
            for name in ensure_list(self.field_extra_fields):
                fields[name] = True

        return list(fields.keys())


    def _collect_parameter_values(self, record):
        values = {}

        for name, query in self.field_params.items():
            if isinstance(query, str):
                values[name] = record[query]
            else:
                data = query.get('data', self.field_data)
                facade = self.command.facade(data, False)
                filters = self._interpolate_values(query.get('filters', {}), record)

                if query.get('order', None):
                    facade.set_order(query['order'])

                if query.get('limit', None):
                    facade.set_limit(query['limit'])

                results = list(facade.field_values(query['field'], **filters))

                if query.get('limit', None) and query['limit'] == 1:
                    values[name] = results[0] if results else None
                else:
                    values[name] = results

        return values


    def _interpolate_values(self, specs, record = None):
        data = {}

        if specs is None:
            specs = {}

        def interpolate(value):
            result = self._replace_pattern(value, record)
            if re.search(r'[\s\(\)]+', value):
                return eval(result)
            return result

        for key, value in specs.items():
            key = re.sub(r'\.', '__', key)

            if isinstance(value, str):
                data[key] = interpolate(value)
            elif isinstance(value, (list, tuple)):
                data[key] = []
                for element in value:
                    data[key].append(interpolate(element))
            else:
                data[key] = value

        return data


    def _replace_pattern(self, pattern, variables):
        if variables is None:
            variables = {}

        parser = ConfigTemplate(pattern)
        try:
            return parser.substitute(**variables).strip()
        except KeyError as e:
            self.command.error("Field {} does not exist".format(e))


    def _validate_value(self, key, value, record):
        success = True

        if self.field_validators:
            for provider, config in self.field_validators.items():
                if not self._run_validator(key, provider, config, value, record):
                    success = False

        return success

    def _run_validator(self, id, provider, config, value, record):
        if config is None:
            config = {}

        config['id'] = "{}:{}".format(self.id, id)
        config['record'] = record

        return self.command.get_provider(
            'validator', provider, config
        ).validate(value)
