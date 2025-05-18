from systems.plugins.index import BaseProvider


class Provider(BaseProvider("source", "csv_file")):
    def load(self):
        return self.load_csv_data_from_file(
            self.field_file,
            self.import_columns,
            archive_file=self.field_archive_file,
            separator=self.field_separator,
            data_type=self.field_data_type,
            header=self.field_header,
        )
