from django.conf import settings
from django.utils.timezone import make_aware

from systems.plugins.index import BasePlugin
from utility.data import ensure_list, serialize, prioritize

import pandas
import datetime
import logging


logger = logging.getLogger(__name__)


class BaseProvider(BasePlugin('source')):

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


    def process(self):
        data_map = prioritize(self.field_data, True)
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

            saved_data = self.validate(name, series)

            if not self.field_disable_save:
                self.save(name, saved_data)

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
            main_facade = self.command.facade(name, False)

            for index, record in enumerate(records):
                add_record = True
                model_data = {}
                scope_filters = {}
                multi_relationships = {}
                warn_on_failure = True

                for field, spec in self.get_relations(name).items():
                    value = self._get_relation_id(spec, index, record)
                    required = spec.get('required', False)

                    if spec.get('multiple', False):
                        facade = self.command.facade(spec['data'], False)
                        related_instances = []

                        if value is not None:
                            for id in value:
                                related_instances.append(facade.retrieve_by_id(id))

                        if related_instances:
                            multi_relationships[field] = related_instances
                        elif required:
                            add_record = False
                    else:
                        if value is not None:
                            scope_filters[field] = value
                        elif not required:
                            scope_filters[field] = None
                        else:
                            add_record = False

                    if not spec.get('warn', True) and not add_record:
                        warn_on_failure = False

                for field, spec in self.get_map(name).items():
                    if not isinstance(spec, dict):
                        spec = { 'column': spec }

                    value = self._get_field_value(spec, index, record)

                    if value is not None:
                        if isinstance(value, datetime.datetime):
                            value = make_aware(value)
                        model_data[field] = value
                    elif not spec.get('required', False):
                        model_data[field] = None
                    else:
                        add_record = False

                key_value = model_data.pop(main_facade.key(), None)
                if add_record:
                    logger.info("Saving {} record for {}: [ {} ] - {}".format(main_facade.name, key_value, scope_filters, model_data))
                    main_facade.set_scope(scope_filters)
                    instance, created = main_facade.store(key_value, **model_data)

                    for field, sub_instances in multi_relationships.items():
                        queryset = getattr(instance, field)
                        for sub_instance in sub_instances:
                            queryset.add(sub_instance)
                else:
                    if warn_on_failure:
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

    def _get_import_columns(self, name = None):
        column_map = {}
        columns = []

        def add_column(column):
            if column not in column_map:
                columns.append(column)
                column_map[column] = True

        def add_columns(data_name):
            for field, column_spec in self.get_map(data_name).items():
                column = self._get_column(column_spec)

                if isinstance(column, (list, tuple)):
                    for component in column:
                        add_column(component)
                else:
                    add_column(column)

            for relation_field, relation_spec in self.get_relations(data_name).items():
                add_column(relation_spec['column'])

        if isinstance(self.field_data, dict):
            if name is None:
                for data_name in self.field_data.keys():
                    add_columns(data_name)
            else:
                add_columns(name)

        return columns


    def _get_relation_id(self, spec, index, record):
        facade = self.command.facade(spec['data'], False)
        value = record[spec['column']]
        key_field = spec.get('key_field', facade.key())
        multiple = spec.get('multiple', False)
        relation_filters = {}
        scope_filters = {}

        if spec.get('scope', False):
            for scope_field, scope_spec in spec['scope'].items():
                if isinstance(scope_spec, dict):
                    scope_filters[scope_field] = self._get_relation_id(scope_spec, index, record)
                else:
                    scope_filters[scope_field] = record[scope_spec] if scope_spec in record else scope_spec

            facade.set_scope(scope_filters)

        if multiple and not isinstance(value, (list, tuple)):
            value = str(value).split(spec.get('separator', ','))

        if 'formatter' in spec:
            value = self._get_formatter_value(index, spec['column'], spec['formatter'], value, record)

        if multiple:
            relation_filters["{}__in".format(key_field)] = value
        else:
            relation_filters[key_field] = value

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
            value = self._get_formatter_value(index, spec['column'], spec['formatter'], value, record)
        return value


    def _validate_relations(self, name, index, record):
        success = True

        for relation_field, relation_spec in self.get_relations(name).items():
            if 'validators' in relation_spec:
                validator_id = "{}:{}:{}".format(name, index, relation_spec['column'])
                column_value = record[relation_spec['column']]

                if relation_spec.get('multiple', False):
                    if not isinstance(column_value, (list, tuple)):
                        separator = relation_spec.get('separator', ',')
                        column_value = str(column_value).split(separator)

                for provider, config in relation_spec['validators'].items():
                    if not self._run_validator(validator_id, provider, config, column_value, record):
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
                    if not self._run_validator(validator_id, provider, config, column_values, record):
                        success = False

        return success


    def _run_validator(self, id, provider, config, value, record):
        if config is None:
            config = {}
        config['id'] = "{}:{}".format(self.id, id)
        return self.command.get_provider(
            'validator', provider, config
        ).validate(value, record)

    def _run_formatter(self, id, provider, config, value, record):
        if config is None:
            config = {}
        config['id'] = "{}:{}".format(self.id, id)
        return self.command.get_provider(
            'formatter', provider, config
        ).format(value, record)

    def _get_formatter_value(self, index, column, spec, value, record):
        if isinstance(spec, str):
            spec = { 'provider': spec }

        return self._run_formatter(
            "{}:{}".format(index, column),
            spec.get('provider', 'base'),
            spec,
            value,
            record
        )
