from systems.plugins.index import BaseProvider


class Provider(BaseProvider('source', 'csv_files')):

    def load(self):
        return self.load_csv_data_from_files(
            self.field_files,
            self.import_columns,
            separator = self.field_separator,
            data_type = self.field_data_type
        )
