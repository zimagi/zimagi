import os
import yaml
import logging


logger = logging.getLogger(__name__)


class ManagerUtilityMixin(object):

    def load_file(self, file_path):
        content = None
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                content = file.read()
        return content

    def load_yaml(self, file_path):
        content = self.load_file(file_path)
        if content:
            content = yaml.safe_load(content)
        return content
