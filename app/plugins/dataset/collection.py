from systems.plugins.index import BaseProvider
from utility.data import ensure_list
from utility.query import init_fields, init_filters
from utility.dataframe import merge


class Provider(BaseProvider('dataset', 'collection')):

    def generate_data(self):
        return self.get_combined_collection(
            query_types = self.field_query_fields,
            required_types = self.field_required_types,
            index_field = self.field_index_field
        )


    def get_record(self, data_type,
        index_field = None,
        fields = None,
        filters = None,
        order = None
    ):
        fields = init_fields(fields)

        if index_field and index_field not in fields:
            fields.append(index_field)

        return self.command.get_data_item(data_type, *fields,
            filters = init_filters(filters),
            order = order,
            dataframe = True,
            dataframe_index_field = index_field
        )

    def get_collection(self, data_type,
        index_field = None,
        fields = None,
        filters = None,
        order = None
    ):
        fields = init_fields(fields)

        if index_field and index_field not in fields:
            fields.append(index_field)

        return self.command.get_data_set(data_type, *fields,
            filters = init_filters(filters),
            order = order,
            dataframe = True,
            dataframe_index_field = index_field
        )


    def get_combined_collection(self, query_types,
        index_field = None,
        required_types = None
    ):
        required_types = ensure_list(required_types) if required_types else None
        required_columns = list()
        collection = list()

        for query_type, params in query_types.items():
            data_type = params.pop('data') if 'data' in params else query_type

            collection_method = getattr(self, "get_{}_collection".format(query_type), None)
            if not collection_method and data_type != query_type:
                collection_method = getattr(self, "get_{}_collection".format(data_type), None)

            method_params = {
                'index_field': index_field,
                **params
            }

            if collection_method:
                data = collection_method(**method_params)
            else:
                data = self.get_collection(data_type, **method_params)

            data.columns = ["{}_{}".format(query_type, column) for column in data.columns]

            if required_types and query_type in required_types:
                required_columns.extend(list(data.columns))

            collection.append(data)

        return merge(*collection,
            required_fields = required_columns,
            ffill = False
        )
