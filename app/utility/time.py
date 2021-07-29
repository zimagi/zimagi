from django.utils.timezone import make_aware

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
        return make_aware(datetime.datetime.now())

    @property
    def now_string(self):
        return self.to_string(self.now)


    def to_string(self, time):
        if isinstance(time, str):
            return time

        if not time.hour and not time.minute and not time.second and not time.microsecond:
            return time.strftime(self.date_format)
        else:
            return time.strftime(self.time_format)


    def to_datetime(self, time):
        if isinstance(time, str):
            try:
                time = datetime.datetime.strptime(time, self.time_format)
            except ValueError:
                time = datetime.datetime.strptime(time, self.date_format)

        if time.tzinfo is None:
            time = make_aware(time)

        return time


    def shift(self, time, units, unit_type = 'days', to_string = False):
        new_time = self.to_datetime(time) + datetime.timedelta(**{
            unit_type: units
        })
        if to_string:
            return self.to_string(new_time)
        return new_time

    def distance(self, time1, time2, unit_type = 'days', include_direction = False):
        time1 = self.to_datetime(time1)
        time2 = self.to_datetime(time2)

        time_span = time2 - time1
        units = getattr(time_span, unit_type)
        return units if include_direction else abs(units)


    def generate(self, start_time, end_time = None, unit_type = 'days', units = None):
        start_time = self.to_datetime(start_time)
        times = []

        if end_time is None:
            if units is None:
                end_time = self.now
            else:
                end_time = self.shift(start_time, units,
                    unit_type = unit_type,
                    to_string = False
                )
        else:
            end_time = self.to_datetime(end_time)

        for index in range(self.distance(start_time, end_time, unit_type = unit_type) + 1):
            times.append(self.shift(start_time, index,
                unit_type = unit_type,
                to_string = True
            ))
        return times
