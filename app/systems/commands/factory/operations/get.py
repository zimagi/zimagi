from utility.data import ensure_list
from utility.python import create_class

from ..helpers import get_facade, get_field_names, get_joined_value, parse_field_names


def GetCommand(parents, base_name, facade_name, view_roles=None):
    _parents = ensure_list(parents)
    _facade_name = get_facade(facade_name)
    _key_field = get_joined_value(base_name, "key")

    def __get_priority(self):
        return 10

    def __get_run_background(self):
        return False

    def __groups_allowed(self):
        from settings.roles import Roles

        return [Roles.admin] + ensure_list(view_roles)

    def __get_epilog(self):
        facade = getattr(self, _facade_name)
        variable = f"{facade.name}_display_fields"
        fields = [x.name for x in reversed(facade.meta.get_fields())]

        return "field display config: {}\n\n> {} fields: {}".format(
            self.header_color(variable), facade.name, self.notice_color(", ".join(fields))
        )

    def __parse(self, add_api_fields=False):
        getattr(self, f"parse_{_key_field}")()
        parse_field_names(self)

    def __exec(self):
        facade = getattr(self, _facade_name)
        instance = getattr(self, base_name)
        self.table(
            self.render_display(facade, getattr(instance, facade.key()), allowed_fields=get_field_names(self)),
            "data",
            row_labels=True,
        )

    def __str__(self):
        return f"Get <{base_name}>"

    attributes = {
        "_resource": facade_name,
        "get_priority": __get_priority,
        "get_run_background": __get_run_background,
        "get_epilog": __get_epilog,
        "parse": __parse,
        "exec": __exec,
        "__str__": __str__,
    }
    if view_roles:
        attributes["groups_allowed"] = __groups_allowed

    return create_class(f"commands.{facade_name}.get", "GetCommand", parents=_parents, attributes=attributes)
