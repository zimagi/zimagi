from systems.plugins.index import BaseProvider
from utility.time import Time


class Provider(BaseProvider("function", "time_range")):
    def exec(self, start_time, end_time, unit_type="days"):
        return Time().generate(start_time, end_time, unit_type)
