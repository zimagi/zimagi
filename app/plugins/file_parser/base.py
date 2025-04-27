from bs4 import BeautifulSoup

from systems.plugins.index import BasePlugin
from utility.filesystem import load_file

import re


class BaseProvider(BasePlugin('file_parser')):

  def check_binary(self):
    return False


  def parse(self, file_path):
    try:
      return self._clean_content(self.parse_file(file_path))
    except Exception as e:
      return ''

  def parse_file(self, file_path):
    return self.parse_content(load_file(file_path, self.check_binary()))

  def parse_content(self, content):
    # Override in subclass
    return content


  def _clean_content(self, content):
    soup = BeautifulSoup(content.encode('ascii', 'ignore').decode().replace("\x00", ''), features = 'html.parser')
    return re.sub(r'\n{3,}', '\n\n', soup.get_text()).strip()
