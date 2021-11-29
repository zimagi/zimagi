from systems.plugins.index import BaseProvider
from utility.time import Time


class Provider(BaseProvider('function', 'time')):

    def exec(self, date_format = '%Y-%m-%d', time_format ='%H:%M:%S', spacer = '.'):
        return Time(
            date_format = date_format,
            time_format = time_format,
            spacer = spacer
        ).now_string
