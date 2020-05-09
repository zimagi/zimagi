from django.conf import settings
from django.utils.module_loading import import_string


class SpecificationIndex(object):

    def __init__(self, manager):
        self.manager = manager
        self.spec = {}
        self.class_map = {}


    def load(self):
        pass

    def print(self):
        pass
