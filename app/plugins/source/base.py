from pandas._libs.tslibs.timestamps import Timestamp
from django.conf import settings
from django.utils.timezone import make_aware

from systems.plugins.index import BasePlugin
from systems.plugins.parser import FormatterParser
from utility.data import ensure_list, serialize, prioritize, get_identifier, dump_json

import pandas
import datetime
import copy
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
        self.state_id = "import:{}:{}".format(id, get_identifier(config))

        self.formatter_parser = FormatterParser(id, command)


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
            if isinstance(data, pandas.DataFrame):
                data = { '_default': data.to_dict('records') }
            self.update_series(data_map, data)
        else:
            data = {}
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
                                data.setdefault(name, [])

                                if info:
                                    if isinstance(info, (list, tuple)):
                                        for sub_record in info:
                                            if sub_record:
                                                data[name].append(sub_record)
                                    else:
                                        data[name].append(info)

                                    if len(data[name]) >= self.page_count:
                                        update = True
                        elif record:
                            data.setdefault('_default', [])
                            data['_default'].append(record)

                            if len(data['_default']) >= self.page_count:
                                update = True

                        if update:
                            self.update_series(data_map, data)
                            data = {}

                self.update_series(data_map, data)
                self.command.delete_state(self.state_id)

    def update_series(self, data_map, data):
        def process_data(name):
            if 'group' in self.field_data[name]:
                series_name = self.field_data[name]['group']
            else:
                series_name = name

            series = data[series_name] if '_default' not in data else data['_default']
            series = copy.deepcopy(series)
            columns = self._get_import_columns(name)

            if isinstance(series, (list, tuple)):
                for index, item in enumerate(series):
                    if isinstance(item, dict):
                        series[index] = [ item[column] for column in columns if column in item ]

                series = self.get_dataframe(series, columns)

            saved_data = self.validate(name, series)
            logger.debug("Importing {}: {}".format(name, saved_data))

            if not self.field_disable_save:
                self.save(name, saved_data)
            else:
                self.command.data(name, dump_json(saved_data, indent = 2))

        if data:
            original_mute = self.command.mute
            self.command.mute = not self.field_disable_save

            for priority, names in sorted(data_map.items()):
                self.command.run_list(names, process_data)

            self.command.mute = original_mute


    def load(self):
        # Override in subclass
        return None # Return a Pandas dataframe unless overriding validate method

    def load_contexts(self):
        # Override in subclass
        return None # Return a list of context values

    def load_items(self, context):
        # Override in subclass
        return [] # Return an iterator that loops over records

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
                    dump_json(record, indent = 2)
                ))

        return saved_data


    def save(self, name, records):
        if records:
            main_facade = self.command.facade(name, False)

            for index, record in enumerate(records):
                add_record = True
                model_data = {}
                scope_relations = {}
                multi_relations = {}
                warn_on_failure = True
                error_messages = []

                for field, spec in self.get_relations(name).items():
                    value = self._get_relation_id(spec, index, record)
                    required = spec.get('required', False)

                    if spec.get('multiple', False):
                        related_instances = []

                        if value is not None:
                            for id in value:
                                related_instances.append(id)

                        if related_instances:
                            multi_relations[field] = related_instances
                        elif required:
                            error_messages.append("Multiple relation field {} is required but does not exist".format(field))
                            add_record = False
                    else:
                        if value is not None:
                            scope_relations[field] = value
                        elif not required:
                            scope_relations[field] = None
                        else:
                            error_messages.append("Relation field {} is required but does not exist".format(field))
                            add_record = False

                    if not spec.get('warn', True) and not add_record:
                        warn_on_failure = False

                for field, spec in self.get_map(name).items():
                    if not isinstance(spec, dict):
                        spec = { 'column': spec }

                    if 'value' in spec:
                        value = spec['value']
                    else:
                        value = self._get_field_value(spec, index, record)

                    if value is not None:
                        model_data[field] = value
                    elif not spec.get('required', False):
                        model_data[field] = None
                    else:
                        error_messages.append("Field {} is required but does not exist".format(field))
                        add_record = False

                key_value = model_data.pop(main_facade.key(), None)
                provider_type = model_data.pop('provider_type', None)

                if add_record:
                    logger.info("Saving {} record for {} {}: [ {} ] - {}".format(main_facade.name, provider_type, key_value, scope_relations, model_data))
                    self.command.save_instance(
                        main_facade, key_value,
                        fields = {
                            **multi_relations,
                            **scope_relations,
                            **model_data,
                            'provider_type': provider_type
                        },
                        quiet = True,
                        normalize = False
                    )
                else:
                    if warn_on_failure:
                        self.command.warning("Failed to update {} {} record {}: {}\n{}".format(
                            self.id,
                            name,
                            "{}:{}".format(key_value, index),
                            dump_json(record, indent = 2, default = str),
                            "\n".join(error_messages)
                        ))


    def _get_column(self, column_spec):
        if isinstance(column_spec, dict):
            return column_spec.get('column', None)
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

                if column:
                    if isinstance(column, (list, tuple)):
                        for component in column:
                            add_column(component)
                    else:
                        add_column(column)

            for relation_field, relation_spec in self.get_relations(data_name).items():
                if 'column' in relation_spec:
                    add_column(relation_spec['column'])

        if isinstance(self.field_data, dict):
            if name is None:
                for data_name in self.field_data.keys():
                    add_columns(data_name)
            else:
                add_columns(name)

        return columns


    def _get_relation_id(self, spec, index, record):
        if 'value' in spec:
            return spec['value']

        facade = self.command.facade(spec['data'], False)
        key_field = spec.get('key_field', facade.key())
        multiple = spec.get('multiple', False)
        relation_filters = {}
        scope_filters = {}
        value = None

        if spec.get('column', None):
            value = record[spec['column']]
        if value is None:
            return value

        if spec.get('scope', False):
            for scope_field, scope_spec in spec['scope'].items():
                if isinstance(scope_spec, dict):
                    scope_filters[scope_field] = self._get_relation_id(scope_spec, index, record)
                elif scope_spec in record:
                    scope_filters[scope_field] = record[scope_spec]
                else:
                    scope_filters[scope_field] = self.formatter_parser.parse(scope_field, scope_spec, record)

            facade.set_scope(scope_filters)

        if value is not None:
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
            column_value = record[column]

            if isinstance(column_value, Timestamp):
                column_value = column_value.to_pydatetime()

            if isinstance(column_value, datetime.datetime):
                if not column_value.tzinfo:
                    record[column] = make_aware(column_value)
                else:
                    record[column] = column_value

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
                    try:
                        column_values.append(record[column])
                    except KeyError:
                        self.command.error("Column {} does not exist for {}: {}".format(
                            column,
                            validator_id,
                            dump_json(record, indent = 2)
                        ))

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
