from django.conf import settings

from systems.plugins.index import ProviderMixin
from systems.commands.args import get_type

import pandas


class CSVSourceMixin(ProviderMixin('csv_source')):

    def load_csv_data_from_file(self, file, columns, separator = ',', data_type = None):
        data_type = self.get_column_type(data_type)
        file_data = pandas.read_csv(
            settings.MANAGER.index.get_module_file(file),
            sep = separator,
            engine = 'python',
            dtype = data_type
        )
        return pandas.DataFrame(file_data, columns = columns, dtype = data_type).drop_duplicates(columns)

    def load_csv_data_from_files(self, files, columns, separator = ',', data_type = None):
        data_type = self.get_column_type(data_type)
        column_data = None
        last_join_column = None

        for join_column, file in files.items():
            file_data = pandas.read_csv(
                settings.MANAGER.index.get_module_file(file),
                sep = separator,
                engine = 'python',
                dtype = data_type
            )

            if column_data is None:
                column_data = file_data
            else:
                column_data = pandas.merge(column_data, file_data,
                    left_on = last_join_column,
                    right_on = join_column
                )
            last_join_column = join_column

        return pandas.DataFrame(column_data, columns = columns, dtype = data_type).drop_duplicates(columns)


    def get_column_type(self, data_type):
        if data_type is None:
            return data_type
        return get_type(data_type)
