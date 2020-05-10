from django.conf import settings
from django.utils.module_loading import import_string

from utility.data import deep_merge

import os
import re
import yaml
import logging


logger = logging.getLogger(__name__)


class SpecificationIndex(object):

    def __init__(self, manager):
        self.manager = manager
        self.spec = {}
        self.class_map = {}


    def load_spec(self):
        def load_directory(base_path):
            for name in os.listdir(base_path):
                file_path = os.path.join(base_path, name)
                if os.path.isdir(file_path):
                    load_directory(file_path)

                elif name[0] != '_' and re.match(r'^[^\.]+\.(yml|yaml)$', name, re.IGNORECASE):
                        logger.debug("Loading specification from file: {}".format(file_path))
                        deep_merge(self.spec, self.manager.load_yaml(file_path))

        for spec_path in self.manager.module_dirs('spec'):
            load_directory(spec_path)

    def print_spec(self):
        print(yaml.dump(self.spec, indent=2))
