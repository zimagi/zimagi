import datetime
from zoneinfo import ZoneInfo

from django.utils.timezone import get_current_timezone, make_aware

from .data import Collection


class TimeException(Exception):
    pass


class Time:
    def __init__(self, timezone=None, date_format="%Y-%m-%d", time_format="%H:%M:%S", spacer="T"):
        self.set_timezone(timezone)

        self.date_format = date_format
        self.time_format = f"{self.date_format}{spacer}{time_format}"

    @property
    def now(self):
        return self.to_datetime(datetime.datetime.now())

    @property
    def now_string(self):
        return self.to_string(self.now)

    @property
    def now_date_string(self):
        return self.to_date_string(self.now)

    @property
    def timezone(self):
        if self._timezone:
            return ZoneInfo(self._timezone)
        else:
            return get_current_timezone()

    def set_timezone(self, timezone):
        self._timezone = timezone

    def to_string(self, date_time, force_date=False):
        if isinstance(date_time, str):
            return date_time

        if force_date or (
            not date_time.hour and not date_time.minute and not date_time.second and not date_time.microsecond
        ):
            return date_time.strftime(self.date_format)
        else:
            return date_time.strftime(self.time_format)

    def to_date_string(self, date_time):
        return self.to_string(date_time, force_date=True)

    def to_datetime(self, date_time):
        if isinstance(date_time, str):
            try:
                date_time = datetime.datetime.strptime(date_time, self.time_format)
            except ValueError:
                date_time = datetime.datetime.strptime(date_time, self.date_format)

        if isinstance(date_time, datetime.datetime):
            if not getattr(date_time, "tzinfo", None) or date_time.tzinfo is None:
                date_time = make_aware(date_time, timezone=self.timezone)
            else:
                date_time.replace(tzinfo=self.timezone)

        return date_time

    def shift(self, date_time, units, unit_type="days", to_string=False):
        new_date_time = self.to_datetime(date_time) + datetime.timedelta(**{unit_type: units})
        if to_string:
            return self.to_string(new_date_time)
        return new_date_time

    def distance(self, date_time1, date_time2, unit_type="days", include_direction=False):
        date_time1 = self.to_datetime(date_time1)
        date_time2 = self.to_datetime(date_time2)

        time_span = date_time2 - date_time1
        units = getattr(time_span, unit_type)
        return units if include_direction else abs(units)

    def generate(self, start_date_time, end_date_time=None, unit_type="days", units=None):
        start_date_time = self.to_datetime(start_date_time)
        times = []

        if end_date_time is None:
            if units is None:
                end_date_time = self.now
            else:
                end_date_time = self.shift(start_date_time, units, unit_type=unit_type, to_string=False)
        else:
            end_date_time = self.to_datetime(end_date_time)

        for index in range(self.distance(start_date_time, end_date_time, unit_type=unit_type) + 1):
            times.append(self.shift(start_date_time, index, unit_type=unit_type, to_string=True))
        return times

    def is_dst(self, date_time):
        non_dst = datetime.datetime(year=date_time.year, month=1, day=1)
        non_dst_tz_aware = non_dst.astimezone(self.timezone)
        return not (non_dst_tz_aware.utcoffset() == date_time.utcoffset())

    def components(self, date_time=None):
        if date_time is None:
            date_time = self.now

        return Collection(
            week=date_time.isocalendar().week,  # starts at 1
            weekday=date_time.isocalendar().weekday,  # starts at 0
            month=date_time.month,
            day=date_time.day,
            hour=date_time.hour,
            minute=date_time.minute,
        )
