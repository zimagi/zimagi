from systems.plugins.index import BaseProvider
from utility.time import Time


class Provider(BaseProvider("function", "time")):
    def exec(self, format="%Y-%m-%dT%H:%M:%S"):
        return Time().now.strftime(format)
