from django.db.models import Aggregate


class Concat(Aggregate):
    function = "STRING_AGG"
    template = "%(function)s(%(distinct)s%(expressions)s, '%(separator)s')"
    allow_distinct = True

    def __init__(self, expression, separator=",", **extra):
        super().__init__(expression, separator=separator, **extra)
