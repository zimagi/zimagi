from rest_framework.exceptions import ParseError
from rest_framework.parsers import BaseParser

from systems.encryption.cipher import Cipher
from utility.data import load_json


class JSONParser(BaseParser):

    media_type = 'application/json'


    def parse(self, stream, media_type, parser_context):
        request = parser_context['request']
        cipher = Cipher.get('data_api',
            user = request.user.name if request.user else None
        )
        try:
            return load_json(cipher.decrypt(stream.read()))

        except ValueError as e:
            raise ParseError("JSON parse error: {}".format(e))
