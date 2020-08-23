from functools import lru_cache

from django.conf import settings

from systems.plugins.index import BasePlugin
from utility.data import ensure_list

import threading
import pandas
import copy


class BaseProvider(BasePlugin('source')):

    thread_lock = threading.Lock()


    def __init__(self, type, name, command, id, config):
        super().__init__(type, name, command)

        self.id = id
        self.config = config
        self.import_columns = self._get_import_columns()

        self.facade_index = settings.MANAGER.index.get_facade_index()
        self.facade = self.facade_index[self.field_data]
        self.key_field = self.facade.key()


    def update(self):
        data = self.load()
        if data is not None:
            self.save(self.validate(data))


    def load(self):
        # Override in subclass
        return None # Return a Pandas dataframe unless overriding validate method


    def validate(self, data):
        saved_data = []

        for index, row in data.iterrows():
            record = row.to_dict()
            relations_ok = self._validate_relations(index, record)
            fields_ok = self._validate_fields(index, record)

            if relations_ok and fields_ok:
                saved_data.append(record)
            else:
                self.command.warning("Skipping {} record {}: {}".format(
                    self.id,
                    index,
                    record
                ))

        return saved_data


    def save(self, records):
        if records:
            for index, record in enumerate(records):
                add_record = True
                model_data = {}

                for field, spec in self.field_relations.items():
                    value = self._get_relation_id(spec, index, record)

                    if value is not None:
                        model_data[field] = value
                    elif not spec.get('required', True):
                        model_data[field] = None
                    else:
                        add_record = False

                for field, spec in self.field_map.items():
                    if not isinstance(spec, dict):
                        spec = { 'column': spec }

                    value = self._get_field_value(spec, index, record)

                    if value is not None:
                        model_data[field] = value
                    elif not spec.get('required', False):
                        model_data[field] = None
                    else:
                        add_record = False

                key_value = model_data.pop(self.key_field, None)
                if key_value and add_record:
                    self.facade.store(key_value, **model_data)
                else:
                    self.command.warning("Failed to update {} record {}: {}".format(
                        self.id,
                        "{}:{}".format(key_value, index),
                        record
                    ))


    def _get_column(self, column_spec):
        if isinstance(column_spec, dict):
            return column_spec['column']
        return column_spec

    @lru_cache(maxsize = None)
    def _get_import_columns(self):
        column_map = {}
        columns = []

        def add_column(column):
            if column not in column_map:
                columns.append(column)
                column_map[column] = True

        for field, column_spec in self.field_map.items():
            column = self._get_column(column_spec)

            if isinstance(column, (list, tuple)):
                for component in column:
                    add_column(component)
            else:
                add_column(column)

        for relation_field, relation_spec in self.field_relations.items():
            add_column(relation_spec['column'])

        return columns


    def _get_relation_id(self, spec, index, record):
        facade = self.facade_index[spec['data']]
        value = record[spec['column']]

        if 'formatter' in spec:
            value = self._get_formatter_value(index, spec['column'], spec['formatter'], value)

        relation_data = list(facade.values(facade.pk, **{
            spec['id']: value
        }))
        if relation_data:
            return relation_data[0][facade.pk]
        return None


    def _get_field_value(self, spec, index, record):
        value = []
        for column in ensure_list(spec['column']):
            value.append(record[column])

        if len(value) == 1:
            value = value[0]

        if 'formatter' in spec:
            value = self._get_formatter_value(index, spec['column'], spec['formatter'], value)
        return value


    def _validate_relations(self, index, record):
        success = True

        for relation_field, relation_spec in self.field_relations.items():
            if 'validators' in relation_spec:
                validator_id = "{}:{}".format(index, relation_spec['column'])
                column_value = record[relation_spec['column']]

                for provider, config in relation_spec['validators'].items():
                    if not self._run_validator(validator_id, provider, config, column_value):
                        success = False

        return success

    def _validate_fields(self, index, record):
        success = True

        for field, column_spec in self.field_map.items():
            if isinstance(column_spec, dict) and 'validators' in column_spec:
                validator_id = "{}:{}".format(index, column_spec['column'])
                column_values = []

                for column in ensure_list(column_spec['column']):
                    column_values.append(record[column])

                if len(column_values) == 1:
                    column_values = column_values[0]

                for provider, config in column_spec['validators'].items():
                    if not self._run_validator(validator_id, provider, config, column_values):
                        success = False

        return success


    def _run_validator(self, id, provider, config, value):
        if config is None:
            config = {}
        config['id'] = "{}:{}".format(self.id, id)
        return self.command.get_provider(
            'validator', provider, config
        ).validate(value)

    def _run_formatter(self, id, provider, config, value):
        if config is None:
            config = {}
        config['id'] = "{}:{}".format(self.id, id)
        return self.command.get_provider(
            'formatter', provider, config
        ).format(value)

    def _get_formatter_value(self, index, column, spec, value):
        if isinstance(spec, str):
            spec = { 'provider': spec }

        return self._run_formatter(
            "{}:{}".format(index, column),
            spec.get('provider', 'base'),
            spec,
            value
        )
