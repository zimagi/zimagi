from .. import exceptions, utility


class OpenAPIJSONCodec(object):

    media_types = ['application/openapi+json', 'application/vnd.oai.openapi+json']


    def decode(self, bytestring, **options):
        try:
            data = utility.load_json(bytestring.decode('utf-8'))
        except ValueError as exc:
            raise exceptions.ParseError("Malformed JSON: {}".format(exc))

        try:
            return data
        except Exception as error:
            raise exceptions.ParseError(error)
