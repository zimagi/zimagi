from systems.plugins.index import BaseProvider
from utility.data import ensure_list
from utility.dataframe import concatenate

import copy


class Provider(BaseProvider('dataset', 'period')):

    def get_provider_config(self):
        return {
            **super().get_provider_config(),
            'time_index': True,
            'start_time': self.field_start_time,
            'end_time': self.field_end_time,
            'unit_type': self.field_unit_type,
            'units': self.field_units,
            'last_known_value': self.field_last_known_value,
            'forward_fill': self.field_forward_fill,
            'resample': self.field_resample,
            'resample_summary': self.field_resample_summary,
            'period_fields': self.field_period_fields
        }


    def initialize_dataset(self, config):
        time_processor = self.get_time_processor()

        if config.start_time:
            if config.end_time:
                config.units = time_processor.distance(config.start_time, config.end_time,
                    unit_type = config.unit_type,
                    include_direction = True
                )
            elif not config.units:
                config.units = time_processor.distance(config.start_time, time_processor.now,
                    unit_type = config.unit_type,
                    include_direction = True
                )


    def initialize_query(self, dataset, config):
        time_processor = self.get_time_processor()

        if config.start_time:
            config.start_time = time_processor.to_datetime(config.start_time)
            if config.units:
                times = [ config.start_time, time_processor.shift(config.start_time, config.units,
                    unit_type = config.unit_type,
                    to_string = False
                ) ]
            else:
                times = [ config.start_time, time_processor.now ]

            config.filters["{}__range".format(config.index_field)] = sorted(times)

    def finalize_query(self, dataset, query):
        time_processor = self.get_time_processor()

        if query.last_known_value and query.start_time:
            if query.units and query.units < 0:
                start_time = time_processor.shift(query.start_time, query.units, unit_type = query.unit_type, to_string = True)
            else:
                start_time = query.start_time

            filters = copy.deepcopy(query.filters)
            filters["{}__lte".format(query.index_field)] = start_time

            data = concatenate(query.dataframe,
                dataset.query_item(query.data, query.fields,
                    index_field = query.index_field,
                    time_index = True,
                    merge_fields = query.merge_fields,
                    remove_fields = query.remove_fields,
                    filters = filters,
                    order = "-{}".format(query.index_field)
                ),
                ffill = query.forward_fill
            )

        if query.resample:
            data = getattr(data.resample(query.resample), query.resample_summary)()

        return data


    def finalize_dataset(self, dataset, data):
        if dataset.resample:
            data = getattr(data.resample(dataset.resample), dataset.resample_summary)()

        if dataset.forward_fill:
            data.ffill(inplace = True)
        else:
            for query_name, query_params in self.field_query_fields.items():
                if 'forward_fill' in query_params:
                    fields = ensure_list(dataset.query_index[query_name])
                    data[fields] = data[fields].ffill()

        if dataset.period_fields:
            data = dataset.extend(data, dataset.period_fields,
                remove_fields = dataset.remove_fields
            )
        return data
