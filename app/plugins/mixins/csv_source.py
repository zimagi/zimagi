from django.conf import settings

from systems.plugins.index import ProviderMixin

import pandas


class CSVSourceMixin(ProviderMixin('csv_source')):

    def load_csv_data_from_file(self, file, columns, separator = ','):
        file_data = pandas.read_csv(
            settings.MANAGER.index.get_module_file(file),
            sep = separator,
            engine = 'python'
        )
        return pandas.DataFrame(file_data, columns = columns).drop_duplicates(columns)

    def load_csv_data_from_files(self, files, columns, separator = ','):
        column_data = None
        last_join_column = None

        for join_column, file in files.items():
            file_data = pandas.read_csv(
                settings.MANAGER.index.get_module_file(file),
                sep = separator,
                engine = 'python'
            )

            if column_data is None:
                column_data = file_data
            else:
                column_data = pandas.merge(column_data, file_data,
                    left_on = last_join_column,
                    right_on = join_column
                )
            last_join_column = join_column

        return pandas.DataFrame(column_data, columns = columns).drop_duplicates(columns)
