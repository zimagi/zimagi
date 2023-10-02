from systems.plugins.index import BaseProvider


class Provider(BaseProvider('validator', 'exists')):

    def validate(self, value, record):
        if value is None:
            self.warning("Value can not be nothing to check for existence")
            return False

        facade = self.command.facade(self.field_data, False)
        filters = {}
        scope_text = ''

        if self.field_scope:
            scope = {}

            for scope_field, scope_value in self.field_scope.items():
                if scope_value in record:
                    scope_value = record[scope_value]
                scope[scope_field] = scope_value

            facade.set_scope(scope)
            scope_text = "within scope {}".format(scope)

        field = self.field_field if self.field_field else facade.key()
        filters[field] = value

        if not facade.keys(**filters):
            self.warning("Model {} {}: {} does not exist {}".format(self.field_data, field, value, scope_text))
            return False
        return True
