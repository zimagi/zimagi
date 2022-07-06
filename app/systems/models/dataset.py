from collections import OrderedDict

from django.conf import settings

from utility.data import Collection, ensure_list, normalize_value, get_identifier
from utility.dataframe import merge
from utility.query import init_fields, init_filters

import re
import pandas


class DataQuery(object):

    def __init__(self, name, config):
        self.name      = name
        self.config    = Collection(**config)
        self.dataframe = None


    def set(self, dataframe):
        if dataframe is not None and len(dataframe.columns) > 0:
            self.dataframe = dataframe
            return True

        self.dataframe = None
        return False

    def __getattr__(self, name):
        if name not in self.config:
            return None
        return self.config[name]


class DataSet(object):

    def __init__(self, command, **config):
        self.command = command
        self.config  = Collection(**config)

        self.required_columns = []
        self.queries          = []
        self.query_index      = {}
        self.separator        = '<<'


    def __getattr__(self, name):
        if name not in self.config:
            return None
        return self.config[name]


    def add(self, query_name, query_params,
        required = False,
        initialize_callback = None,
        finalize_callback = None
    ):
        query = DataQuery(query_name, {
            **self.config.export(),
            'data': query_name,
            **query_params
        })
        query.config.fields = init_fields(query.fields or [])

        if query.index_field and query.index_field not in query.fields:
            query.config.fields.append(query.index_field)

        if initialize_callback and callable(initialize_callback):
            initialize_callback(self, query.config)

        data = self.query(query.data, query.fields,
            index_field = query.index_field,
            time_index = query.time_index,
            merge_fields = query.merge_fields,
            remove_fields = query.remove_fields,
            filters = init_filters(query.filters or {}),
            limit = query.limit if query.limit else 0,
            order = query.order
        )
        if query.set(data):
            if query.prefix_column:
                data.columns = [ "{}_{}".format(query_name, column) for column in data.columns ]

            if finalize_callback and callable(finalize_callback):
                data = finalize_callback(self, query)

            if query.processors:
                for processor in ensure_list(query.processors):
                    data = self._exec_data_processor(processor, data)

            if required:
                self.required_columns.extend(list(data.columns))

            self.query_index[query_name] = list(data.columns)
            self.queries.append(query)
            query.set(data)


    def render(self, callback = None,):
        if not self.queries:
            return None

        data = merge(*[ query.dataframe for query in self.queries ],
            required_fields = self.required_columns,
            ffill = False
        )
        if callback and callable(callback):
            data = callback(self, data)

        if self.config.processors:
            for processor in ensure_list(self.config.processors):
                data = self._exec_data_processor(processor, data)

        return data


    def extend(self, data, field_definitions, remove_fields = None):
        field_info, removals = self._collect_fields(field_definitions)
        remove_fields = ensure_list(remove_fields) if remove_fields else []

        for field, info in field_info.items():
            if info and 'processor' in info:
                data[field] = self._exec_field_processor(info['processor'], data, data[info['field']], **info['options'])

        if remove_fields:
            for field in remove_fields:
                if field in data.columns:
                    data.drop(field, axis = 1, inplace = True)

        return data


    def query(self, data_type, fields,
        index_field = None,
        time_index = False,
        merge_fields = None,
        remove_fields = None,
        filters = None,
        limit = 0,
        order = None
    ):
        if not fields or (index_field and len(fields) == 1 and fields[0] == index_field):
            return None

        for index, field in enumerate(fields):
            fields[index] = "".join(field.split())

        annotations          = self._parse_annotations(fields)
        aggregates           = list(annotations.keys())
        field_info, removals = self._collect_fields(fields)

        facade = self.command.facade(data_type, False)
        facade.set_limit(limit)
        facade.set_order(order)
        facade.set_annotations(**annotations)

        if index_field and merge_fields:
            return self._get_merged_dataframe(facade, field_info,
                index_field = index_field,
                time_index = time_index,
                filters = filters,
                merge_fields = merge_fields,
                aggregates = aggregates,
                removals = remove_fields + removals if remove_fields else removals
            )

        return self._get_dataframe(facade, field_info,
            index_field = index_field,
            time_index = time_index,
            filters = filters,
            aggregates = aggregates,
            removals = remove_fields + removals if remove_fields else removals
        )


    def query_item(self, data_type, fields,
        index_field = None,
        time_index = False,
        merge_fields = None,
        remove_fields = None,
        filters = None,
        order = None
    ):
        return self.query(data_type, fields,
            index_field = index_field,
            time_index = time_index,
            merge_fields = merge_fields,
            remove_fields = remove_fields,
            filters = filters,
            order = order,
            limit = 1
        )


    def _parse_fields(self, fields, callback):
        for index, field in enumerate(fields):
            field_components = [ component.strip() for component in field.split(self.separator) ]
            field_name       = field_components[0]
            field_definition = field_components[1] if len(field_components) > 1 else field_components[0]

            callback(field_name, field_definition)


    def _parse_annotations(self, fields):
        annotations = {}

        def add_annotations(field_name, field_definition):
            # field_name << element:AGGREGATOR_FUNCTION([param = value[, ...]])
            match = re.match(r'^([^\:]+)\:([A-Z0-9]+)(?:\(\s*([^\)]*)\s*\))?$', field_definition.strip())
            if match:
                aggregated_field = match[1]
                aggregator_function = match[2]
                aggregator_params = match[3]
                aggregator_options = {}

                if aggregator_params:
                    for parameter in [ component.strip() for component in aggregator_params.split(';') ]:
                        name, value = tuple([ element.strip() for element in parameter.split('=') ])
                        aggregator_options[name] = normalize_value(value, True, True)

                annotations[field_name] = [ aggregator_function, aggregated_field, aggregator_options ]

        self._parse_fields(fields, add_annotations)
        return annotations


    def _collect_fields(self, fields):
        field_info = OrderedDict()
        removals   = []

        def generate_field_info(field_name, field_definition):
            field_info[field_name] = {}

            # field_name << element
            # field_name << field_processor(element[, param = value[, ...]])
            match = re.match(r'^([^\(\:]+)(?:\(\s*([^\s\;\)]+)(?:\s*\,\s*([^\)]*))?\))?$', field_definition.strip())
            if match:
                field_processor = match[1]
                processed_field = match[2]
                processor_params = match[3]
                processor_options = {}

                if field_processor and not processed_field:
                    processed_field = field_processor
                    field_processor = None
                    info = { 'field': processed_field }
                else:
                    if processor_params:
                        for parameter in [ parameter.strip() for parameter in processor_params.split(';') ]:
                            name, value = tuple([ element.strip() for element in parameter.split('=') ])
                            processor_options[name] = normalize_value(value, True, True)

                    info = {
                        'processor': field_processor,
                        'field': processed_field,
                        'options': processor_options
                    }

                if field_processor or field_name != processed_field:
                    if processed_field not in field_info:
                        field_info[processed_field] = {}
                        removals.append(processed_field)

                    field_info[field_name] = info

        self._parse_fields(fields, generate_field_info)
        return field_info, removals


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
        merge_fields = ensure_list(merge_fields) if merge_fields is not None else []
        merge_filter_index = {}
        dataframe = None

        if not filters:
            filters = {}

        for merge_filters in list(facade.values(*merge_fields, **filters)):
            merge_values = self._get_merge_values(merge_fields, merge_filters)
            merge_filter_id = get_identifier(merge_values)

            if merge_filter_id not in merge_filter_index:
                sub_dataframe = self._get_dataframe(facade, field_info,
                    index_field = index_field,
                    time_index = time_index,
                    filters = {**filters, **merge_filters},
                    aggregates = aggregates,
                    removals = removals
                )

                value_prefix = "_".join(merge_values)
                sub_dataframe.columns = ["{}_{}".format(value_prefix, column) for column in sub_dataframe.columns]

                if dataframe is None:
                    dataframe = sub_dataframe
                else:
                    dataframe = dataframe.merge(sub_dataframe, how = "outer", left_index = True, right_index = True)

                merge_filter_index[merge_filter_id] = True

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


    def _exec_data_processor(self, name, dataset, **options):
        return self.command.get_provider('data_processor', name).exec(dataset, **options)

    def _exec_field_processor(self, name, dataset, field_data, **options):
        return self.command.get_provider('field_processor', name).exec(dataset, field_data, **options)
