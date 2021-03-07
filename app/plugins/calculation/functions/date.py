from datetime import datetime, timedelta


def date(date_str, format = '%Y-%m-%d'):
    return datetime.strptime(date_str, format)

def time(time_str, format = '%Y-%m-%d %H:%M:%S'):
    return datetime.strptime(time_str, format)


def weeks(weeks):
    return timedelta(weeks = weeks)

def days(days):
    return timedelta(days = days)

def hours(hours):
    return timedelta(hours = hours)

def minutes(min):
    return timedelta(minutes = min)

def seconds(sec):
    return timedelta(seconds = sec)
