from django.conf import settings

from systems.plugins.index import BasePlugin
from plugins.parser.config import ConfigTemplate
from utility.data import ensure_list

import threading
import importlib
import glob
import re
import logging


logger = logging.getLogger(__name__)


for directory in settings.MANAGER.index.get_module_dirs('plugins/calculation/functions'):
    for function_file in glob.glob("{}/*.py".format(directory)):
        spec = importlib.util.spec_from_file_location("module.name", function_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        for function in dir(module):
            globals()[function] = getattr(module, function)


class ParameterData(object):

    def __init__(self, data = None):
        self.parameters = {}
        if isinstance(data, dict):
            self.parameters = data

    def __getattr__(self, name):
        return self.parameters.get(name, None)


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


    def process(self, reset):
        facade = self.command.facade(self.field_data, False)
        for item in self.load_items(facade, reset):
            self.process_item(facade, item)


    def load_items(self, facade, reset):
        filters = self._generate_filters(self.field_filters)
        if not reset:
            filters["{}__isnull".format(self.field_field)] = True

        return facade.values(*self._collect_fields(facade), **filters)

    def process_item(self, facade, record):
        key = record[facade.key()]
        params = ParameterData(self._collect_parameter_values(record))
        value = self.calc(params)

        if self._validate_value(key, value):
            if not self.field_disable_save:
                instance = facade.retrieve_by_id(record[facade.pk])
                setattr(instance, self.field_field, value)
                instance.save()
        else:
            self.command.warning("Skipping {} {} value {}: {}".format(
                self.id,
                key,
                value,
                record
            ))


    def _collect_fields(self, facade):
        fields = {
            facade.pk: True,
            facade.key(): True,
            self.field_field: True
        }

        for name, info in self.field_params.items():
            if isinstance(info, str):
                fields[info] = True
            else:
                for query, values in info.get('filters', {}).items():
                    for value in ensure_list(values):
                        if isinstance(value, str):
                            match = re.search(r'^\{\{([^\}]+)\}\}$', value.strip())
                            if match:
                                field_expression = match.group(1)
                                # TODO: Handle expressions
                                fields[field_expression] = True

                for field in ensure_list(info.get('order', [])):
                    fields[re.sub(r'^[~-]', '', field)] = True

        return list(fields.keys())


    def _collect_parameter_values(self, record):
        values = {}

        for name, query in self.field_params.items():
            if isinstance(query, str):
                values[name] = record[query]
            else:
                data = query.get('data', self.field_data)
                facade = self.command.facade(data, False)
                filters = self._generate_filters(query.get('filters', {}), record)

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


    def _generate_filters(self, filter_specs, record = None):
        filters = {}

        if filter_specs is None:
            filter_specs = {}

        def interpolate(value):
            result = self._replace_pattern(value, record)
            if not re.match(r'^\@?[a-zA-Z0-9\-\_]+$', result):
                return eval(result)
            return result

        for filter_key, filter_value in filter_specs.items():
            filter_key = re.sub(r'\.', '__', filter_key)

            if isinstance(filter_value, str):
                filters[filter_key] = interpolate(filter_value)
            elif isinstance(filter_value, (list, tuple)):
                filters[filter_key] = []
                for element in filter_value:
                    filters[filter_key].append(interpolate(element))

        return filters


    def _replace_pattern(self, pattern, variables):
        if variables is None:
            variables = {}

        parser = ConfigTemplate(pattern)
        try:
            return parser.substitute(**variables).strip()
        except KeyError as e:
            self.command.error("Field {} does not exist".format(e))


    def _validate_value(self, key, value):
        success = True

        if self.field_validators:
            for provider, config in self.field_validators.items():
                if not self._run_validator(key, provider, config, value):
                    success = False

        return success

    def _run_validator(self, id, provider, config, value):
        if config is None:
            config = {}
        config['id'] = "{}:{}".format(self.id, id)
        return self.command.get_provider(
            'validator', provider, config
        ).validate(value)
