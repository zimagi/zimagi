from systems.plugins.index import BaseProvider


class Provider(BaseProvider('file_parser', 'binary')):

  def check_binary(self):
    return True

  def parse_content(self, content):
    # Override in subclass
    raise NotImplementedError("All binary file parsers must implement the parse_content method.")
