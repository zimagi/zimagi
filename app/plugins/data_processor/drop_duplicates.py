from systems.plugins.index import BaseProvider


class Provider(BaseProvider("data_processor", "drop_duplicates")):
    def exec(self, dataset):
        return dataset.drop_duplicates()
