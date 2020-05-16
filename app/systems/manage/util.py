import os
import oyaml
import logging


logger = logging.getLogger(__name__)


class ManagerUtilityMixin(object):

    def __init__(self):
        super().__init__()


    def load_file(self, file_path):
        content = None
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                content = file.read()
        return content

    def load_yaml(self, file_path):
        content = self.load_file(file_path)
        if content:
            content = oyaml.safe_load(content)
        return content
