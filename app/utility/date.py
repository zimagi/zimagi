import datetime


class Date(object):

    def __init__(self, date_format = '%Y-%m-%d'):
        self.format = date_format


    @property
    def today(self):
        return datetime.datetime.now()

    @property
    def today_string(self):
        return self.to_string(self.today)


    def to_string(self, date):
        if isinstance(date, str):
            return date
        return date.strftime(self.format)

    def to_date(self, date):
        if isinstance(date, str):
            return datetime.datetime.strptime(date, self.format)
        return date


    def shift(self, date, days, to_string = False):
        new_date = self.to_date(date) + datetime.timedelta(days = days)
        if to_string:
            return self.to_string(new_date)
        return new_date

    def distance(self, date1, date2, include_direction = False):
        date1 = self.to_date(date1)
        date2 = self.to_date(date2)
        time_span = date2 - date1
        return time_span.days if include_direction else abs(time_span.days)


    def generate(self, start_date, end_date = None, days = None):
        start_date = self.to_date(start_date)
        dates = []

        if end_date is None:
            if days is None:
                end_date = self.today
            else:
                end_date = self.shift(start_date, days)
        else:
            end_date = self.to_date(end_date)

        for index in range(self.distance(start_date, end_date) + 1):
            dates.append(self.shift(start_date, index, True))

        return dates
