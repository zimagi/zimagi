from django.utils.timezone import make_aware, get_current_timezone

import datetime


class TimeException(Exception):
    pass


class Time(object):

    def __init__(self,
        date_format = "%Y-%m-%d",
        time_format = "%H:%M:%S",
        spacer = ' '
    ):
        self.date_format = date_format
        self.time_format = "{}{}{}".format(
            self.date_format,
            spacer,
            time_format
        )


    @property
    def now(self):
        return self.to_datetime(datetime.datetime.now())

    @property
    def now_string(self):
        return self.to_string(self.now)


    def to_string(self, date_time):
        if isinstance(date_time, str):
            return date_time

        if not date_time.hour and not date_time.minute and not date_time.second and not date_time.microsecond:
            return date_time.strftime(self.date_format)
        else:
            return date_time.strftime(self.time_format)


    def to_datetime(self, date_time):
        if isinstance(date_time, str):
            try:
                date_time = datetime.datetime.strptime(date_time, self.time_format)
            except ValueError:
                date_time = datetime.datetime.strptime(date_time, self.date_format)

        if date_time.tzinfo is None:
            date_time = make_aware(date_time, is_dst = self.is_dst(date_time))

        return date_time


    def shift(self, date_time, units, unit_type = 'days', to_string = False):
        new_date_time = self.to_datetime(date_time) + datetime.timedelta(**{
            unit_type: units
        })
        if to_string:
            return self.to_string(new_date_time)
        return new_date_time

    def distance(self, date_time1, date_time2, unit_type = 'days', include_direction = False):
        date_time1 = self.to_datetime(date_time1)
        date_time2 = self.to_datetime(date_time2)

        time_span = date_time2 - date_time1
        units = getattr(time_span, unit_type)
        return units if include_direction else abs(units)


    def generate(self, start_date_time, end_date_time = None, unit_type = 'days', units = None):
        start_date_time = self.to_datetime(start_date_time)
        times = []

        if end_date_time is None:
            if units is None:
                end_date_time = self.now
            else:
                end_date_time = self.shift(start_date_time, units,
                    unit_type = unit_type,
                    to_string = False
                )
        else:
            end_date_time = self.to_datetime(end_date_time)

        for index in range(self.distance(start_date_time, end_date_time, unit_type = unit_type) + 1):
            times.append(self.shift(start_date_time, index,
                unit_type = unit_type,
                to_string = True
            ))
        return times


    def is_dst(self, date_time):
        non_dst = datetime.datetime(year = date_time.year, month = 1, day = 1)
        non_dst_tz_aware = get_current_timezone().localize(non_dst)
        return not (non_dst_tz_aware.utcoffset() == date_time.utcoffset())