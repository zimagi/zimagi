from docx2python import docx2python

from systems.plugins.index import BaseProvider


class Provider(BaseProvider('file_parser', 'docx')):

  def parse_file(self, file_path):
    with docx2python(file_path, html = False) as docx:
      return docx.text
