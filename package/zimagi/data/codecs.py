from .. import exceptions, utility

import pandas


class OpenAPIJSONCodec(object):

    media_types = ['application/openapi+json', 'application/vnd.oai.openapi+json']

    def decode(self, bytestring, **options):
        try:
            data = utility.load_json(bytestring.decode('utf-8'))

        except ValueError as exc:
            raise exceptions.ParseError("Malformed JSON: {}".format(exc))
        return data


class CSVCodec(object):

    media_types = ['text/csv']

    def decode(self, bytestring, **options):
        try:
            csv_data = self._get_csv_data(bytestring.decode('utf-8'))
            if csv_data:
                data = pandas.DataFrame(csv_data[1:], columns = csv_data[0])
            else:
                data = pandas.DataFrame()

        except ValueError as exc:
            raise exceptions.ParseError("Malformed CSV: {}".format(exc))
        return data


    def _get_csv_data(self, csv_string):
        csv_data = []
        for csv_line in csv_string.strip('\\n').split('\\n'):
            csv_line = csv_line.lstrip("\'\"").rstrip("\'\"")
            if csv_line:
                csv_data.append([
                    utility.normalize_value(value.strip(), strip_quotes = True)
                    for value in csv_line.split(',')
                ])
        return csv_data