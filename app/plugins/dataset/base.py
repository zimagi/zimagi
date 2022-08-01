from django.conf import settings
from django.utils.module_loading import import_string

from systems.plugins.index import BasePlugin
from utility.environment import Environment
from utility.time import Time
from utility.filesystem import filesystem_dir
from utility.dataframe import get_csv_file_name

import os
import pandas
import copy


class BaseProvider(BasePlugin('dataset')):

    @property
    def _filesystem(self):
        return filesystem_dir(os.path.join(settings.DATASET_BASE_PATH, Environment.get_active_env()))


    def preprocess_fields(self, fields, instance = None):
        defined_fields = [ *self.facade.fields, *self.get_fields() ]
        query_fields = {}

        for query_field in list(fields.keys()):
            if ':' in query_field or query_field not in defined_fields:
                field_components = query_field.split(':')
                query_type = field_components[0]
                field = field_components[1] if len(field_components) > 1 else None
                value = fields.pop(query_field)

                if query_type not in query_fields:
                    query_fields[query_type] = {}

                if isinstance(value, str) and ',' in value:
                    value = value.split(',')

                if field:
                    query_fields[query_type][field] = value

        if query_fields:
            fields['query_fields'] = query_fields

        if instance and 'query_fields' in fields:
            instance.config = copy.deepcopy(self.config)

        return fields


    def initialize_instance(self, instance, created):
        if self.field_query_fields:
            data = self.query_dataset()
            if data is not None:
                self.save_data(instance.name, data)
                self.command.notice(data)

    def finalize_instance(self, instance):
        self.remove_data(instance.name)


    def get_time_processor(self):
        return Time(
            date_format = settings.DEFAULT_DATE_FORMAT,
            time_format = settings.DEFAULT_TIME_FORMAT,
            spacer = settings.DEFAULT_TIME_SPACER_FORMAT
        )


    def get_provider_config(self):
        return {
            'index_field': self.field_index_field,
            'merge_fields': self.field_merge_fields,
            'remove_fields': self.field_remove_fields,
            'prefix_column_query': self.field_prefix_column_query,
            'prefix_column_identity': self.field_prefix_column_identity,
            'processors': self.field_processors
        }

    def initialize_dataset(self, config):
        # Override in subclass if needed
        pass

    def finalize_dataset(self, dataset, data):
        # Override in subclass if needed
        return data

    def initialize_query(self, config):
        # Override in subclass if needed
        pass

    def finalize_query(self, query):
        # Override in subclass if needed
        return query.dataframe


    def query_dataset(self):
        required_types = self.field_required_types if self.field_required_types else []

        try:
            dataset_class = import_string(self.field_dataset_class)
        except ImportError as e:
            self.command.error("DataSet class {} not found: {}".format(self.field_dataset_class, e))

        dataset = dataset_class(self.command, **self.get_provider_config())
        self.initialize_dataset(dataset.config)

        for query_name, query_params in self.field_query_fields.items():
            dataset.add(query_name, query_params,
                required = query_name in required_types,
                initialize_callback = self.initialize_query,
                finalize_callback = self.finalize_query
            )
        return dataset.render(callback = self.finalize_dataset)


    def load(self, **options):
        instance = self.check_instance('dataset load')
        return self.load_data(instance.name, **options)

    def load_data(self, name, index_column = None, sort_index = True, **options):
        with self._filesystem as filesystem:
            data = pandas.read_csv(filesystem.path(get_csv_file_name(name)), index_col = index_column, **options)

            if sort_index:
                data = data.sort_index()

        return data


    def save_data(self, name, data, **options):
        with self._filesystem as filesystem:
            filesystem.save(
                data.to_csv(date_format = self.get_time_processor().time_format, **options),
                get_csv_file_name(name)
            )


    def remove_data(self, name):
        with self._filesystem as filesystem:
            filesystem.remove(get_csv_file_name(name))
