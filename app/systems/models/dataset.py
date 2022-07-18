from collections import OrderedDict

from django.conf import settings

from utility.data import Collection, ensure_list, normalize_value
from utility.dataframe import merge

import re
import pandas


ASSIGNMENT_SEPARATOR           = '<<'
PARAMETER_SEPARATOR            = ';'
PARAMETER_ASSIGNMENT_SEPARATOR = '='


class DataQuery(object):

    def __init__(self, command, name, config):
        self.command = command

        self.name      = name
        self.config    = Collection(**config)

        self.merge_identities = []
        self.dataframe        = None

        if not self.config.fields:
            self.config.fields = []
        if not self.config.filters:
            self.config.filters = {}


    def __getattr__(self, name):
        if name not in self.config:
            return None
        return self.config[name]

    def __setattr__(self, name, value):
        if name in ('command', 'name', 'config', 'merge_identities', 'dataframe'):
            self.__dict__[name] = value
        else:
            self.config[name] = value


    def clone(self):
        instance = DataQuery(
            self.command,
            self.name,
            self.config.export()
        )
        instance.merge_identities = self.merge_identities
        instance.dataframe        = self.dataframe
        return instance


    def empty(self):
        return True if self.dataframe is None or len(self.dataframe.columns) == 0 else False


    def execute(self):
        if not self.fields or (self.index_field and len(self.fields) == 1 and self.fields[0] == self.index_field):
            return None

        for index, field in enumerate(self.fields):
            self.fields[index] = "".join(field.split())

        self.merge_identities = []

        annotations          = self.parse_annotations(self.fields)
        aggregates           = list(annotations.keys())
        field_info, removals = self.collect_fields(self.fields)

        facade = self.command.facade(self.data, False)
        facade.set_limit(self.limit or 0)
        facade.set_order(self.order)
        facade.set_annotations(**annotations)

        if self.index_field and self.merge_fields:
            self.dataframe = self._get_merged_dataframe(facade, field_info,
                index_field = self.index_field,
                time_index = self.time_index,
                filters = self.filters,
                merge_fields = self.merge_fields,
                aggregates = aggregates,
                removals = self.remove_fields + removals if self.remove_fields else removals
            )
        else:
            self.dataframe = self._get_dataframe(facade, field_info,
                index_field = self.index_field,
                time_index = self.time_index,
                filters = self.filters,
                aggregates = aggregates,
                removals = self.remove_fields + removals if self.remove_fields else removals
            )

        if not self.empty():
            if self.prefix_column:
                self.dataframe.columns = [ "{}_{}".format(self.name, column) for column in self.dataframe.columns ]

        return self.dataframe


    def get_record(self):
        self.limit = 1
        if self.order and self.index_field:
            self.order = "-{}".format(self.index_field)
        return self.execute()


    @classmethod
    def process_fields(cls, fields, callback):
        for index, field in enumerate(fields):
            field_components = [ component.strip() for component in field.split(ASSIGNMENT_SEPARATOR) ]
            field_name       = field_components[0]
            field_definition = field_components[1] if len(field_components) > 1 else field_components[0]

            callback(field_name, field_definition)


    @classmethod
    def parse_annotations(cls, fields):
        annotations = {}

        def add_annotations(field_name, field_definition):
            # field_name << element:AGGREGATOR_FUNCTION([param = value[; ...]])
            match = re.match(r'^([^\:]+)\:([A-Z0-9]+)(?:\(\s*([^\)]*)\s*\))?$', field_definition.strip())
            if match:
                aggregated_field = match[1]
                aggregator_function = match[2]
                aggregator_params = match[3]

                annotations[field_name] = [ aggregator_function, aggregated_field, cls.parse_params(aggregator_params) ]

        cls.process_fields(fields, add_annotations)
        return annotations


    @classmethod
    def collect_fields(cls, fields):
        field_info = OrderedDict()
        removals   = []

        def generate_field_info(field_name, field_definition):
            field_info[field_name] = {}

            # field_name << element
            # field_name << field_processor(element[; param = value[; ...]])
            match = re.match(r'^([^\(\:]+)(?:\(\s*([^\s\;\)]+)(?:\s*\,\s*([^\)]*))?\))?$', field_definition.strip())
            if match:
                field_processor = match[1]
                processed_field = match[2]
                processor_params = match[3]

                if field_processor and not processed_field:
                    processed_field = field_processor
                    field_processor = None
                    info = { 'field': processed_field }
                else:
                    info = {
                        'processor': field_processor,
                        'field': processed_field,
                        'options': cls.parse_params(processor_params)
                    }

                if field_processor or field_name != processed_field:
                    if processed_field not in field_info:
                        field_info[processed_field] = {}
                        removals.append(processed_field)

                    field_info[field_name] = info

        cls.process_fields(fields, generate_field_info)
        return field_info, removals


    @classmethod
    def parse_params(cls, param_string):
        options = {}

        def parse_value(value, separator):
            return re.sub(r'\\\\{}'.format(separator), '\\{}'.format(separator),
                re.sub(r'(?<!\\)\\{}'.format(separator), separator, value)
            )

        if param_string:
            for parameter in [ parameter.strip() for parameter in re.split(r'(?<!\\){}'.format(PARAMETER_SEPARATOR), param_string) ]:
                name, value = tuple([ element.strip() for element in re.split(r'(?<!\\){}'.format(PARAMETER_ASSIGNMENT_SEPARATOR), parameter) ])
                value = parse_value(value, PARAMETER_SEPARATOR)
                value = parse_value(value, PARAMETER_ASSIGNMENT_SEPARATOR)
                options[name] = normalize_value(value, True, True)

        return options


    def _get_dataframe(self, facade, field_info,
        index_field = None,
        time_index = False,
        filters = None,
        aggregates = None,
        removals = None
    ):
        if not filters:
            filters = {}
        if not removals:
            removals = []

        dataframe = facade.dataframe(*self._get_query_fields(facade, field_info, aggregates), **filters)

        for field, info in field_info.items():
            if info:
                if 'processor' in info:
                    dataframe[field] = self._exec_field_processor(info['processor'], dataframe, dataframe[info['field']], **info['options'])
                elif info['field'] != field:
                    dataframe.rename({ info['field']: field }, axis = 'columns', inplace = True)

        if index_field:
            if time_index:
                dataframe[index_field] = pandas.to_datetime(dataframe[index_field], utc = True)
                dataframe[index_field] = dataframe[index_field].dt.tz_convert(settings.TIME_ZONE)

            dataframe.set_index(index_field, inplace = True, drop = True)

        if removals:
            for field in removals:
                if field in dataframe.columns:
                    dataframe.drop(field, axis = 1, inplace = True)

        return dataframe


    def _get_merged_dataframe(self, facade, field_info,
        index_field = None,
        time_index = False,
        filters = None,
        merge_fields = None,
        aggregates = None,
        removals = None
    ):
        merge_fields = facade._parse_fields(ensure_list(merge_fields)) if merge_fields is not None else []
        merge_filter_index = {}
        dataframe = None

        if not filters:
            filters = {}

        for merge_filters in list(facade.values(*merge_fields, **filters)):
            merge_values = self._get_merge_values(merge_fields, merge_filters)
            value_prefix = "_".join(merge_values)

            if value_prefix not in merge_filter_index:
                sub_dataframe = self._get_dataframe(facade, field_info,
                    index_field = index_field,
                    time_index = time_index,
                    filters = {**filters, **merge_filters},
                    aggregates = aggregates,
                    removals = removals
                )
                sub_dataframe.columns = ["{}_{}".format(value_prefix, column) for column in sub_dataframe.columns]

                if dataframe is None:
                    dataframe = sub_dataframe
                else:
                    dataframe = dataframe.merge(sub_dataframe, how = "outer", left_index = True, right_index = True)

                self.merge_identities.append(value_prefix)
                merge_filter_index[value_prefix] = True

        return dataframe


    def _get_query_fields(self, facade, field_info, aggregates = None):
        fields = []

        if not aggregates:
            aggregates = []

        for field, info in field_info.items():
            if '__' in field or field in facade.fields or field in aggregates:
                fields.append(field)

        return fields

    def _get_merge_values(self, merge_fields, merge_filters):
        values = []

        for merge_field in ensure_list(merge_fields):
            values.append(re.sub(r'[^a-z0-9]+', '', str(merge_filters[merge_field]).lower()))

        return values


    def _exec_field_processor(self, name, dataset, field_data, **options):
        return self.command.get_provider('field_processor', name).exec(dataset, field_data, **options)


class DataSet(object):

    def __init__(self, command, **config):
        self.command = command
        self.config  = Collection(**config)

        self.required_columns = []
        self.queries          = []
        self.query_index      = {}


    def __getattr__(self, name):
        if name not in self.config:
            return None
        return self.config[name]


    def add(self, query_name, query_params,
        required = False,
        initialize_callback = None,
        finalize_callback = None
    ):
        query = DataQuery(self.command, query_name, {
            **self.config.export(),
            'data': query_name,
            **query_params
        })
        if query.index_field and query.index_field not in query.fields:
            query.fields.append(query.index_field)

        if initialize_callback and callable(initialize_callback):
            initialize_callback(query.config)

        query.execute()

        if not query.empty():
            if finalize_callback and callable(finalize_callback):
                query.dataframe = finalize_callback(query.clone())

            if query.processors:
                for info in self._collect_data_processors(query.processors):
                    query.dataframe = self._exec_data_processor(info['processor'], query.dataframe, **info['options'])

            if required:
                self.required_columns.extend(list(query.dataframe.columns))

            self.query_index[query_name] = list(query.dataframe.columns)
            self.queries.append(query)


    def render(self, callback = None,):
        if not self.queries:
            return None

        data = merge(*[ query.dataframe for query in self.queries ],
            required_fields = self.required_columns,
            ffill = False
        )
        if data is not None and not data.empty:
            if callback and callable(callback):
                data = callback(self, data)

            if self.config.processors:
                for info in self._collect_data_processors(self.config.processors):
                    data = self._exec_data_processor(info['processor'], data, **info['options'])

        return data


    def extend(self, data, field_definitions, remove_fields = None):
        remove_fields = ensure_list(remove_fields) if remove_fields else []

        def exec_field_processor(info, identity_field, source_field):
            data[identity_field] = self._exec_field_processor(info['processor'], data, data[source_field], **info['options'])

        self._process_data_fields(field_definitions, exec_field_processor)

        if remove_fields:
            for field in remove_fields:
                if field in data.columns:
                    data.drop(field, axis = 1, inplace = True)

        return data


    def _exec_field_processor(self, name, dataset, field_data, **options):
        return self.command.get_provider('field_processor', name).exec(dataset, field_data, **options)

    def _exec_data_processor(self, name, dataset, **options):
        return self.command.get_provider('data_processor', name).exec(dataset, **options)


    def _process_data_fields(self, field_definitions, callback):
        field_info, removals = DataQuery.collect_fields(field_definitions)
        merge_identities = {}
        query_token = '<query>'
        identity_token = '<identity>'

        def render_field(field_template, **variables):
            return re.sub(r"<([^>]*)>", r"{\1}", field_template).format(**variables)

        def render_fields(identity_template, source_template, **variables):
            identity_field = render_field(identity_template, **variables)
            source_field   = render_field(source_template, **variables)
            return identity_field, source_field

        for query in self.queries:
            merge_identities[query.name] = query.merge_identities

        for field, info in field_info.items():
            if info and 'processor' in info and 'field' in info:
                if query_token in field:
                    if identity_token in field:
                        for query_name, identities in merge_identities.items():
                            for identity in identities:
                                identity_field, source_field = render_fields(field, info['field'],
                                    query = query_name,
                                    identity = identity
                                )
                                callback(info, identity_field, source_field)
                    else:
                        for query_name, identities in merge_identities.items():
                            for identity in identities:
                                if identity in field:
                                    break

                            identity_field, source_field = render_fields(field, info['field'],
                                query = query_name,
                                identity = identity
                            )
                            callback(info, identity_field, source_field)

                elif identity_token in field:
                    query_name = field.split(identity_token)[0].strip('_')
                    for identity in merge_identities[query_name]:
                        identity_field, source_field = render_fields(field, info['field'],
                            query = query_name,
                            identity = identity
                        )
                        callback(info, identity_field, source_field)
                else:
                    callback(info, field, info['field'])


    def _collect_data_processors(self, processors):
        processor_info = []

        for processor_definition in processors:
            # data_processor[(param = value[; ...])]
            match = re.match(r'^([^\(]+)(?:\(\s*([^\)]*)\))?$', processor_definition.strip())
            if match:
                data_processor = match[1]
                processor_params = match[2]

                if data_processor:
                    processor_info.append({
                        'processor': data_processor,
                        'options': DataQuery.parse_params(processor_params)
                    })
        return processor_info
