from collections import OrderedDict

from django.http import HttpResponse

import csv


class CSVExport():

    def __init__(self, data = {}):
        self._process_data(data)


    def set(self, data):
        self._process_data(data)


    def send(self, file_name):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(file_name)

        writer = csv.writer(response)

        for row in self._generate_headers():
            writer.writerow(row)

        for record in self._generate_records():
            writer.writerow(record)

        return response


    def _process_data(self, data):
        self.data = data
        self.dates = []
        self.fields = OrderedDict()
        fields = {}

        for date in sorted(data.keys()):
            instruments = data[date]

            self.dates.append(date)

            for instrument, field_data in instruments.items():
                if instrument not in self.fields:
                    fields[instrument] = []

                for field in field_data.keys():
                    if field not in fields[instrument]:
                        fields[instrument].append(field)

        for instrument in sorted(fields.keys()):
            self.fields[instrument] = sorted(fields[instrument])


    def _generate_headers(self):
        instruments = ['']
        fields = ['date']

        for instrument, data_fields in self.fields.items():
            for field in data_fields:
                instruments.append(instrument)
                fields.append(field)

        return [instruments, fields]

    def _generate_records(self):
        records = []

        for date in self.dates:
            row = [date]

            for instrument, data_fields in self.fields.items():
                for field in data_fields:
                    row.append(self._get_value(self.data[date][instrument], field))

            records.append(row)

        return records


    def _get_value(self, data, field):
        try:
            return data[field]
        except Exception:
            return None
