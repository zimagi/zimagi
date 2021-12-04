from systems.plugins.index import BaseProvider


class Provider(BaseProvider('field_processor', 'combined_text')):

    def exec(self, dataset, field_data, append = None, separator = ","):
        if append:
            for field in append.split(','):
                field_data = field_data.str.cat(
                    dataset[field].astype(str),
                    sep = separator
                )

        return field_data
