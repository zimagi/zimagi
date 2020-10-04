from functools import lru_cache

from django.conf import settings

from systems.plugins.index import BasePlugin
from utility.data import ensure_list, serialize

import threading
import pandas
import copy


class BaseProvider(BasePlugin('source')):

    thread_lock = threading.Lock()
    page_count = 100


    def __init__(self, type, name, command, id, config):
        super().__init__(type, name, command)

        self.id = id
        self.config = config
        self.import_columns = self._get_import_columns()

        self.facade_index = settings.MANAGER.index.get_facade_index()
        self.state_id = "import:{}".format(id)


    def get_relations(self, name):
        return self.field_data[name].get('relations', {})

    def get_map(self, name):
        return self.field_data[name].get('map', {})

    def get_dataframe(self, series, columns):
        return pandas.DataFrame(list(series), columns = list(columns))


    def update(self):
        data_map = self._order_data(self.field_data)
        data = self.load()

        if data is not None:
            self.update_series(data_map, data)
        else:
            data = self.update_series(data_map)
            contexts = self.load_contexts()
            if contexts is None:
                contexts = ['all']

            next_id = self.command.get_state(self.state_id)
            process = False if next_id else True

            for context in list(contexts):
                context_id = serialize(context)
                if next_id and context_id == next_id:
                    process = True

                if process:
                    self.command.set_state(self.state_id, context_id)

                    items = self.load_items(context) # Items should be iterator, not list
                    for item in items:
                        record = self.load_item(item, context)
                        update = False

                        if isinstance(record, dict):
                            for name, info in record.items():
                                if info:
                                    if isinstance(info[0], (list, tuple)):
                                        for sub_record in info:
                                            if sub_record:
                                                data[name].append(list(sub_record))
                                    else:
                                        data[name].append(list(info))

                                    if len(data[name]) >= self.page_count:
                                        update = True
                        elif record:
                                data.append(list(record))
                                if len(data) >= self.page_count:
                                    update = True

                        if update:
                            data = self.update_series(data_map, data)

                self.update_series(data_map, data)
                self.command.delete_state(self.state_id)

    def update_series(self, data_map, data = None):
        column_info = self.item_columns()

        def process_data(name):
            columns = column_info[name] if isinstance(column_info, dict) else column_info
            series = data[name] if isinstance(data, dict) else data

            if isinstance(series, (list, tuple)):
                series = self.get_dataframe(series, columns)
            self.save(name, self.validate(name, series))

        if data is not None:
            for priority, names in sorted(data_map.items()):
                self.command.run_list(names, process_data)

        if isinstance(column_info, dict):
            data = {}
            for name, column_names in column_info.items():
                data[name] = []
        else:
            data = []

        return data


    def load(self):
        # Override in subclass
        return None # Return a Pandas dataframe unless overriding validate method

    def load_contexts(self):
        # Override in subclass
        return None # Return a list of context values

    def load_items(self, context):
        # Override in subclass
        return [] # Return an iterator that loops over records

    def item_columns(self):
        # Override in subclass
        return [] # Return a list of column names or a dictionary of names column sets

    def load_item(self, item, context):
        # Override in subclass
        return [] # Return a list of record values or a dictionary of named record values


    def validate(self, name, data):
        saved_data = []

        for index, row in data.iterrows():
            record = row.to_dict()
            relations_ok = self._validate_relations(name, index, record)
            fields_ok = self._validate_fields(name, index, record)

            if relations_ok and fields_ok:
                saved_data.append(record)
            else:
                self.command.warning("Skipping {} {} record {}: {}".format(
                    self.id,
                    name,
                    index,
                    record
                ))

        return saved_data


    def save(self, name, records):
        if records:
            main_facade = self.facade_index[name]

            for index, record in enumerate(records):
                add_record = True
                model_data = {}
                multi_relationships = {}

                for field, spec in self.get_relations(name).items():
                    value = self._get_relation_id(spec, index, record)

                    if spec.get('multiple', False):
                        facade = self.facade_index[spec['data']]
                        related_instances = []

                        if value is not None:
                            for id in value:
                                related_instances.append(facade.retrieve_by_id(id))

                        if related_instances:
                            multi_relationships[field] = related_instances
                        elif spec.get('required', False):
                            add_record = False
                    else:
                        if value is not None:
                            model_data[field] = value
                        elif not spec.get('required', False):
                            model_data[field] = None
                        else:
                            add_record = False

                for field, spec in self.get_map(name).items():
                    if not isinstance(spec, dict):
                        spec = { 'column': spec }

                    value = self._get_field_value(spec, index, record)

                    if value is not None:
                        model_data[field] = value
                    elif not spec.get('required', False):
                        model_data[field] = None
                    else:
                        add_record = False

                key_value = model_data.pop(main_facade.key(), None)
                if key_value and add_record:
                    instance, created = main_facade.store(key_value, **model_data)

                    for field, sub_instances in multi_relationships.items():
                        queryset = getattr(instance, field)
                        for sub_instance in sub_instances:
                            with instance.facade.thread_lock:
                                queryset.add(sub_instance)
                else:
                    self.command.warning("Failed to update {} {} record {}: {}".format(
                        self.id,
                        name,
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

        for name in self.field_data.keys():
            for field, column_spec in self.get_map(name).items():
                column = self._get_column(column_spec)

                if isinstance(column, (list, tuple)):
                    for component in column:
                        add_column(component)
                else:
                    add_column(column)

            for relation_field, relation_spec in self.get_relations(name).items():
                add_column(relation_spec['column'])

        return columns


    def _get_relation_id(self, spec, index, record):
        facade = self.facade_index[spec['data']]
        value = record[spec['column']]
        multiple = spec.get('multiple', False)

        if multiple:
            value = str(value).split(spec.get('separator', ','))

        if 'formatter' in spec:
            value = self._get_formatter_value(index, spec['column'], spec['formatter'], value)

        if multiple:
            relation_filters = { "{}__in".format(facade.key()): value }
        else:
            relation_filters = { facade.key(): value }

        relation_data = list(facade.values(facade.pk, **relation_filters))
        value = None

        if relation_data:
            if multiple:
                value = []
                for item in relation_data:
                    value.append(item[facade.pk])
            else:
                value = relation_data[0][facade.pk]

        return value


    def _get_field_value(self, spec, index, record):
        value = []
        for column in ensure_list(spec['column']):
            value.append(record[column])

        if len(value) == 1:
            value = value[0]

        if 'formatter' in spec:
            value = self._get_formatter_value(index, spec['column'], spec['formatter'], value)
        return value


    def _validate_relations(self, name, index, record):
        success = True

        for relation_field, relation_spec in self.get_relations(name).items():
            if 'validators' in relation_spec:
                validator_id = "{}:{}:{}".format(name, index, relation_spec['column'])
                column_value = record[relation_spec['column']]

                if relation_spec.get('multiple', False):
                    separator = relation_spec.get('separator', ',')
                    column_value = column_value.split(separator)

                for provider, config in relation_spec['validators'].items():
                    if not self._run_validator(validator_id, provider, config, column_value):
                        success = False

        return success

    def _validate_fields(self, name, index, record):
        success = True

        for field, column_spec in self.get_map(name).items():
            if isinstance(column_spec, dict) and 'validators' in column_spec:
                validator_id = "{}:{}:{}".format(name, index, column_spec['column'])
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


    def _order_data(self, spec):
        dependencies = {}
        priorities = {}
        priority_map = {}

        if isinstance(spec, dict):
            for name, config in spec.items():
                if config is not None and isinstance(config, dict):
                    requires = ensure_list(config.get('requires', []))
                    dependencies[name] = requires

            for name, requires in dependencies.items():
                priorities[name] = 0

            for index in range(0, len(dependencies.keys())):
                for name in list(dependencies.keys()):
                    for require in dependencies[name]:
                        priorities[name] = max(priorities[name], priorities[require] + 1)

            for name, priority in priorities.items():
                if priority not in priority_map:
                    priority_map[priority] = []
                priority_map[priority].append(name)

        return priority_map
