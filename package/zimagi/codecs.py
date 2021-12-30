from collections import OrderedDict

from . import exceptions

import json


class JSONCodec(object):

    media_type = 'application/json'


    def decode(self, bytestring, **options):
        try:
            return json.loads(
                bytestring.decode('utf-8'),
                object_pairs_hook = OrderedDict
            )
        except ValueError as exc:
            raise exceptions.ParseError("Malformed JSON: {}".format(exc))
