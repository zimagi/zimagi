import copy
import re

import pandas
from django.conf import settings
from utility.data import Collection, ensure_list
from utility.dataframe import merge

from .parsers.data_processors import DataProcessorParser
from .parsers.field_processors import FieldProcessorParser


def get_processors(processors):
    if not processors:
        return []
    return [DataProcessorParser().evaluate(processor) for processor in processors]


class DataQuery:
    def __init__(self, command, name, config):
        self.command = command

        self.name = name
        self.config = Collection(**config)

        self.merge_identities = []

        self.facade = self.command.facade(self.data, False)
        self.dataframe = None

        self.config.fields = ensure_list(self.config.fields) if self.config.fields else []
        self.config.order = ensure_list(self.config.order) if self.config.order else []

        if not self.config.filters:
            self.config.filters = {}

    def __getattr__(self, name):
        if name not in self.config:
            return None
        return self.config[name]

    def __setattr__(self, name, value):
        if name in ("command", "name", "config", "merge_identities", "facade", "dataframe"):
            self.__dict__[name] = value
        else:
            self.config[name] = value

    def clone(self):
        instance = DataQuery(self.command, self.name, self.config.export())
        instance.merge_identities = copy.deepcopy(self.merge_identities)
        instance.facade = copy.deepcopy(self.facade)
        instance.dataframe = self.dataframe
        return instance

    def empty(self):
        return True if self.dataframe is None or len(self.dataframe.columns) == 0 else False

    def execute(self):
        if not self.fields or (self.index_field and len(self.fields) == 1 and self.fields[0] == self.index_field):
            return None

        self.merge_identities = []

        self.facade.set_limit(self.limit or 0)
        self.facade.set_order(self.order)

        if self.index_field and self.merge_fields:
            self.dataframe = self._get_merged_dataframe()
        else:
            self.dataframe = self._get_dataframe(self.filters)

        if not self.empty():
            if self.prefix_column_query:
                self.dataframe.columns = [f"{self.name}_{column}" for column in self.dataframe.columns]

        return self.dataframe

    def get_record(self):
        self.limit = 1
        if self.order and self.index_field:
            self.order = f"-{self.index_field}"
        return self.execute()

    def _get_dataframe(self, filters):
        dataframe = self.facade.dataframe(*self.fields, **filters)

        if self.index_field:
            if self.time_index:
                dataframe[self.index_field] = pandas.to_datetime(dataframe[self.index_field], utc=True)
                dataframe[self.index_field] = dataframe[self.index_field].dt.tz_convert(settings.TIME_ZONE)

            dataframe.set_index(self.index_field, inplace=True, drop=True)

        if self.remove_fields:
            for field in self.remove_fields:
                if field in dataframe.columns:
                    dataframe.drop(field, axis=1, inplace=True)

        return dataframe

    def _get_merged_dataframe(self):
        merge_fields = self.facade.parse_fields(self.merge_fields) if self.merge_fields is not None else []
        merge_filter_index = {}
        dataframe = None

        for merge_filters in list(self.facade.values(*merge_fields, **self.filters)):
            merge_values = self._get_merge_values(merge_fields, merge_filters)
            value_prefix = "_".join(merge_values)

            if value_prefix not in merge_filter_index:
                sub_dataframe = self._get_dataframe({**self.filters, **merge_filters})

                if self.prefix_column_identity:
                    sub_dataframe.columns = [f"{value_prefix}_{column}" for column in sub_dataframe.columns]

                if dataframe is None:
                    dataframe = sub_dataframe
                else:
                    dataframe = dataframe.merge(sub_dataframe, how="outer", left_index=True, right_index=True)

                self.merge_identities.append(value_prefix)
                merge_filter_index[value_prefix] = True

        return dataframe

    def _get_merge_values(self, merge_fields, merge_filters):
        values = []

        for merge_field in ensure_list(merge_fields):
            values.append(re.sub(r"[^a-z0-9]+", "", str(merge_filters[merge_field]).lower()))

        return values


class DataSet:
    def __init__(self, command, **config):
        self.command = command
        self.config = Collection(**config)

        self.required_columns = []
        self.queries = []
        self.query_index = {}

    def __getattr__(self, name):
        if name not in self.config:
            return None
        return self.config[name]

    def add(self, query_name, query_params, required=False, initialize_callback=None, finalize_callback=None):
        query = DataQuery(self.command, query_name, {**self.config.export(), "data": query_name, **query_params})
        if query.index_field and query.index_field not in query.fields:
            query.fields.append(query.index_field)

        if initialize_callback and callable(initialize_callback):
            initialize_callback(query.config)

        query.execute()

        if not query.empty():
            if finalize_callback and callable(finalize_callback):
                query.dataframe = finalize_callback(query.clone())

            for processor in get_processors(query.processors):
                query.dataframe = self._exec_data_processor(processor, query.dataframe)

            if required:
                self.required_columns.extend(list(query.dataframe.columns))

            self.query_index[query_name] = list(query.dataframe.columns)
            self.queries.append(query)

    def render(
        self,
        callback=None,
    ):
        if not self.queries:
            return None

        data = merge(*[query.dataframe for query in self.queries], required_fields=self.required_columns, ffill=False)
        if data is not None and not data.empty:
            if callback and callable(callback):
                data = callback(self, data)

            if self.config.processors:
                for processor in get_processors(self.config.processors):
                    data = self._exec_data_processor(processor, data)
        return data

    def extend(self, data, fields, remove_fields=None):
        remove_fields = ensure_list(remove_fields) if remove_fields else []

        def exec_field_processor(processor):
            data[processor.name] = self._exec_field_processor(processor, data)

        self._process_data_fields(fields, exec_field_processor)

        if remove_fields:
            for field in remove_fields:
                if field in data.columns:
                    data.drop(field, axis=1, inplace=True)

        return data

    def _exec_data_processor(self, processor, dataset):
        return self.command.get_provider("data_processor", processor.provider).exec(
            dataset, *processor.args, **processor.options
        )

    def _exec_field_processor(self, processor, dataset):
        return self.command.get_provider("field_processor", processor.provider).exec(
            dataset, dataset[processor.field], *processor.args, **processor.options
        )

    def _process_data_fields(self, fields, callback):
        merge_identities = {query.name: query.merge_identities for query in self.queries}
        parser = FieldProcessorParser()
        query_token = "<query>"
        identity_token = "<identity>"

        def render_field(field_template, **variables):
            return re.sub(r"<([^>]*)>", r"{\1}", field_template).format(**variables)

        for field in fields:
            if query_token in field:
                for query_name, identities in merge_identities.items():
                    if identity_token in field:
                        for identity in identities:
                            rendered_field = render_field(field, query=query_name, identity=identity)
                            callback(parser.evaluate(rendered_field))
                    else:
                        rendered_field = render_field(field, query=query_name)
                        callback(parser.evaluate(rendered_field))

            elif identity_token in field:
                query_name = field.split(identity_token)[0].strip("_")
                query_names = [query_name] if query_name else list(merge_identities.keys())

                for query_name in query_names:
                    for identity in merge_identities[query_name]:
                        rendered_field = render_field(field, query=query_name, identity=identity)
                        callback(parser.evaluate(rendered_field))
            else:
                callback(parser.evaluate(field))
