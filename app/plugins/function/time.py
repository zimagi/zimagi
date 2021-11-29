from systems.plugins.index import BaseProvider
from utility.time import Time


class Provider(BaseProvider('function', 'time')):

    def exec(self):
        return Time(
            date_format = "%Y-%m-%d",
            time_format = "%H:%M:%S",
            spacer = "."
        ).now_string
