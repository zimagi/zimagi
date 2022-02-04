from . import exceptions, collection, utility


class JSONCodec(object):

    media_types = ['application/json']


    def decode(self, bytestring, **options):

        def convert(data):
            if isinstance(data, dict):
                data = collection.RecursiveCollection(data)
            elif isinstance(data, (list, tuple)):
                for index, value in enumerate(data):
                    data[index] = convert(value)
            return data

        try:
            return convert(utility.load_json(bytestring.decode('utf-8')))

        except ValueError as error:
            raise exceptions.ParseError("Malformed JSON: {}".format(error))
