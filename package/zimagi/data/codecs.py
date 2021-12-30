from openapi_core import create_spec

from .. import exceptions

import json


class OpenAPIJSONCodec(object):

    media_type = 'application/openapi+json'
    media_types = ['application/openapi+json', 'application/vnd.oai.openapi+json']


    def decode(self, bytestring, **options):
        base_url = options.get('base_url')
        try:
            data = json.loads(bytestring.decode('utf-8'))
        except ValueError as exc:
            raise exceptions.DataParseError("Malformed JSON: {}".format(exc))

        try:
            return create_spec(data)
        except Exception as error:
            raise exceptions.DataParseError(error)
