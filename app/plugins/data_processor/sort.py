from systems.plugins.index import BaseProvider


class Provider(BaseProvider('data_processor', 'sort')):

    def exec(self, dataset, *fields):
        columns = []
        ascending = []

        for field in fields:
            field_ascending = True

            if field[0] == '~' or field[0] == '-':
                field = field[1:]
                field_ascending = False

            columns.append(field)
            ascending.append(field_ascending)

            dataset.sort_values(
                by = columns,
                inplace = True,
                ascending = ascending
            )
        return dataset
