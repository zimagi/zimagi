from systems.plugins.index import BasePlugin
from utility.data import get_identifier

import billiard as multiprocessing


class BaseProvider(BasePlugin('sentence_parser')):

    lock = multiprocessing.Lock()


    def __init__(self, type, name, command, init = True, **options):
        super().__init__(type, name, command)
        self.import_config(options)

        self.identifier = self._get_identifier(init)

        with self.lock:
            self.initialize(self, init)


    @classmethod
    def initialize(cls, instance, init):
        raise NotImplementedError("Class initialize method required by all subclasses")


    def _get_identifier(self, init):
        return get_identifier([ '1' if init else '0', self.name, self.field_device ])

    def get_max_sentence_length(self):
        return self.field_max_sentence_length


    def split(self, text, **config):
        raise NotImplementedError("Class split method required by all subclasses")
