from systems.plugins.index import BaseProvider


class Provider(BaseProvider('source', 'csv_file')):

    def load(self):
        return self.load_csv_data_from_file(
            self.field_file,
            self.import_columns
        )
