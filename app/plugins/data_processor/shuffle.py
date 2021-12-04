from sklearn.utils import shuffle

from systems.plugins.index import BaseProvider


class Provider(BaseProvider('data_processor', 'shuffle')):

    def exec(self, dataset):
        return shuffle(dataset)
