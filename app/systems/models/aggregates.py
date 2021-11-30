from django.db.models import Aggregate, CharField, Value


class Concat(Aggregate):

    function = 'GROUP_CONCAT'
    template = '%(function)s(%(expressions)s)'


    def __init__(self, expression, delimiter = ',', **extra):
        output_field = extra.pop('output_field', CharField())
        delimiter = Value(delimiter)

        super().__init__(expression, delimiter, output_field = output_field, **extra)


    def as_postgresql(self, compiler, connection):
        self.function = 'STRING_AGG'
        return super().as_sql(compiler, connection)
