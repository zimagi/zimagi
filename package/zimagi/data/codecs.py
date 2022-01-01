from openapi_core import create_spec

from .. import exceptions

import json


class OpenAPIJSONCodec(object):

    media_types = ['application/openapi+json', 'application/vnd.oai.openapi+json']


    def decode(self, bytestring, **options):
        try:
            data = json.loads(bytestring.decode('utf-8'))
        except ValueError as exc:
            raise exceptions.ParseError("Malformed JSON: {}".format(exc))

        try:
            return create_spec(data)
        except Exception as error:
            raise exceptions.ParseError(error)
