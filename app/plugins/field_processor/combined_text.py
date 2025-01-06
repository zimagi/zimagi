from systems.plugins.index import BaseProvider
from utility.data import load_json


class Provider(BaseProvider("field_processor", "combined_text")):
    def exec(self, dataset, field_data, append=None, separator=","):
        if append:
            if isinstance(append, str):
                append = load_json(append) if append[0] == "[" else append.split(",")

            for field in append:
                field_data = field_data.str.cat(dataset[field].astype(str), sep=separator)
        return field_data
