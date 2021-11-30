from django.db.models import Aggregate


class Concat(Aggregate):

    function = 'GROUP_CONCAT'
    template = "%(function)s(%(distinct)s%(expressions)s)"
    allow_distinct = True


    def __init__(self, expression, separator = ';', **extra):
        super().__init__(expression,
            separator = separator,
            **extra
        )


    def as_postgresql(self, compiler, connection):
        self.function = 'STRING_AGG'
        self.template = "%(function)s(%(distinct)s%(expressions)s, '%(separator)s')"
        return super().as_sql(compiler, connection)

    def as_mysql(self, compiler, connection):
        self.template = "%(function)s(%(distinct)s%(expressions)s SEPARATOR '%(separator)s')"
        return super().as_sql(compiler, connection)

    def as_sqlite(self, compiler, connection):
        self.template = "%(function)s(REPLACE(%(distinct)s%(expressions)s, '', ''), '%(separator)s')"
        return super().as_sql(compiler, connection)
