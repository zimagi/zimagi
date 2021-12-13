from systems.plugins.index import BaseProvider


class Provider(BaseProvider('data_processor', 'shuffle')):

    def exec(self, dataset):
        return dataset.sample(frac = 1)
