from django.conf import settings

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
            data = self.generate_data()
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


    def generate_data(self):
        # Override in subclass
        return None


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


    def exec_function(self, name, *args, **options):
        return self.command.get_provider('function', name).exec(*args, **options)
