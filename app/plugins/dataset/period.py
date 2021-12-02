from django.utils.timezone import make_aware

from systems.plugins.index import BaseProvider
from utility.data import ensure_list
from utility.query import init_fields, init_filters
from utility.dataframe import merge, concatenate

import copy


class Provider(BaseProvider('dataset', 'period')):

    def generate_data(self):
        return self.get_combined_period(
            query_types = self.field_query_fields,
            required_types = self.field_required_types,
            index_field = self.field_index_field,
            merge_fields = self.field_merge_fields,
            remove_fields = self.field_remove_fields,
            column_prefix = self.field_column_prefix,
            processors = self.field_processors,
            start_time = self.field_start_time,
            end_time = self.field_end_time,
            unit_type = self.field_unit_type,
            units = self.field_units,
            last_known_value = self.field_last_known_value,
            forward_fill = self.field_forward_fill,
            resample = self.field_resample,
            resample_summary = self.field_resample_summary
        )


    def get_record(self, data_type, time,
        index_field = 'created',
        merge_fields = None,
        remove_fields = None,
        fields = None,
        filters = None,
        recent = False
    ):
        fields = init_fields(fields)
        filters = init_filters(filters)

        if index_field not in fields:
            fields.append(index_field)

        time = self.get_time_processor().to_datetime(time)
        if recent:
            filters["{}__lte".format(index_field)] = time
        else:
            filters[index_field] = time

        return self.command.get_data_item(data_type, *fields,
            filters = filters,
            order = "-{}".format(index_field),
            dataframe = True,
            dataframe_index_field = index_field,
            dataframe_merge_fields = merge_fields,
            dataframe_remove_fields = remove_fields,
            time_index = True
        )

    def get_period(self, data_type,
        index_field = 'created',
        merge_fields = None,
        remove_fields = None,
        start_time = None,
        unit_type = 'days',
        units = None,
        fields = None,
        filters = None,
        last_known_value = True,
        forward_fill = False,
        resample = None,
        resample_summary = 'last'
    ):
        fields = init_fields(fields)
        filters = init_filters(filters)
        range_filters = copy.deepcopy(filters)
        time_processor = self.get_time_processor()

        if index_field not in fields:
            fields.append(index_field)

        if start_time:
            start_time = time_processor.to_datetime(start_time)
            if units:
                times = [start_time, time_processor.shift(start_time, units,
                    unit_type = unit_type,
                    to_string = False
                )]
            else:
                times = [start_time, time_processor.now]

            range_filters["{}__range".format(index_field)] = sorted(times)

        data = self.command.get_data_set(data_type, *fields,
            filters = range_filters,
            order = index_field,
            dataframe = True,
            dataframe_index_field = index_field,
            dataframe_merge_fields = merge_fields,
            dataframe_remove_fields = remove_fields,
            time_index = True
        )

        if last_known_value and start_time:
            start_time = time_processor.shift(start_time, units, unit_type = unit_type, to_string = True) if units and units < 0 else start_time
            data = concatenate(data,
                self.get_record(data_type, start_time,
                    index_field = index_field,
                    merge_fields = merge_fields,
                    remove_fields = remove_fields,
                    fields = fields,
                    filters = filters,
                    recent = True
                ),
                ffill = forward_fill
            )

        if resample:
            data = getattr(data.resample(resample), resample_summary)()

        return data


    def get_combined_period(self, query_types,
        index_field = 'created',
        merge_fields = None,
        remove_fields = None,
        column_prefix = True,
        processors = None,
        start_time = None,
        end_time = None,
        unit_type = 'days',
        units = None,
        required_types = None,
        last_known_value = True,
        forward_fill = False,
        resample = None,
        resample_summary = 'last'
    ):
        required_types = ensure_list(required_types) if required_types else None
        time_processor = self.get_time_processor()
        required_columns = list()
        periods = list()
        field_map = {}

        if start_time:
            if end_time:
                units = time_processor.distance(start_time, end_time,
                    unit_type = unit_type,
                    include_direction = True
                )
            elif not units:
                units = time_processor.distance(start_time, time_processor.now,
                    unit_type = unit_type,
                    include_direction = True
                )

        for query_type, params in query_types.items():
            data_type = params.pop('data', query_type)
            prefix = params.pop('column_prefix', column_prefix)
            functions = params.pop('processors', processors)

            period_method = getattr(self, "get_{}_period".format(query_type), None)
            if not period_method and data_type != query_type:
                period_method = getattr(self, "get_{}_period".format(data_type), None)

            method_params = {
                'index_field': index_field,
                'merge_fields': merge_fields,
                'remove_fields': remove_fields,
                'start_time': start_time,
                'unit_type': unit_type,
                'units': units,
                'last_known_value': last_known_value,
                **params
            }

            if period_method:
                data = period_method(**method_params)
            else:
                data = self.get_period(data_type, **method_params)

            if prefix:
                data.columns = ["{}_{}".format(query_type, column) for column in data.columns]

            if functions:
                for function in functions:
                    data = self.exec_function(function, data)

            field_map[query_type] = list(data.columns)

            if required_types and query_type in required_types:
                required_columns.extend(list(data.columns))

            periods.append(data)

        data = merge(*periods,
            required_fields = required_columns,
            ffill = False
        )
        if resample:
            data = getattr(data.resample(resample), resample_summary)()

        if forward_fill:
            data.ffill(inplace = True)
        else:
            for query_type, params in query_types.items():
                if 'forward_fill' in params:
                    fields = ensure_list(field_map[query_type])
                    data[fields] = data[fields].ffill()

        return data
