from systems.plugins.index import BaseProvider


class Provider(BaseProvider("data_processor", "drop_na")):
    def exec(self, dataset):
        return dataset.dropna()
