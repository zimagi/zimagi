from django.conf import settings

from systems.plugins.index import BasePlugin
from utility.data import ensure_list

import threading
import pandas


class BaseProvider(BasePlugin('source')):

    thread_lock = threading.Lock()


    def __init__(self, type, name, command, config):
        super().__init__(type, name, command)

        self.config = config
        self.import_columns = self._get_import_columns()

        self.facade_index = settings.MANAGER.index.get_facade_index()
        self.facade = self.facade_index[self.field_data]
        self.key_field = self.facade.key()
        self.required_fields = ensure_list(self.field_required_fields)


    def update(self):
        self.save(self.load())


    def load(self):
        # Override in subclass
        return None # Return a Pandas dataframe unless overriding save method

    def save(self, data):
        for index, row in data.iterrows():
            add_model = True
            record = row.to_dict()
            print(record)

            model_data = {}
            for field, column in self.field_map.items():
                if not pandas.isnull(record[column]) or field not in self.required_fields:
                    model_data[field] = record[column]
                else:
                    add_model = False

            if add_model:
                for relation_field, relation_spec in self.field_relations.items():
                    relation_facade = self.facade_index[relation_spec['data']]
                    relation_data = list(relation_facade.values(relation_facade.pk, **{
                        relation_spec['id']: record[relation_spec['column']]
                    }))
                    if relation_data or relation_field not in self.required_fields:
                        model_data[relation_field] = relation_data[0][relation_facade.pk]
                    else:
                        add_model = False

            if add_model:
                print(model_data)
                key_value = model_data.pop(self.key_field)
                self.facade.store(key_value, **model_data)


    def _get_import_columns(self):
        columns = list(self.field_map.values())
        for relation_field, relation_spec in self.field_relations.items():
            columns.append(relation_spec['column'])
        return columns
