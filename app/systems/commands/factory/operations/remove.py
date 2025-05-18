from utility.data import ensure_list
from utility.python import create_class

from ..helpers import get_facade, get_joined_value


def RemoveCommand(parents, base_name, facade_name, edit_roles=None):
    _parents = ensure_list(parents)
    _facade_name = get_facade(facade_name)
    _key_field = get_joined_value(base_name, "key")

    def __get_priority(self):
        return 20

    def __get_run_background(self):
        return False

    def __groups_allowed(self):
        from settings.roles import Roles

        return [Roles.admin] + ensure_list(edit_roles)

    def __parse(self, add_api_fields=False):
        self.parse_force()
        getattr(self, f"parse_{_key_field}")()

    def __confirm(self):
        return True

    def __exec(self):
        facade = getattr(self, _facade_name)
        self.set_scope(facade, True)

        self.remove_instance(facade, getattr(self, _key_field))

    def __str__(self):
        return f"Remove <{base_name}>"

    attributes = {
        "_resource": facade_name,
        "get_priority": __get_priority,
        "get_run_background": __get_run_background,
        "parse": __parse,
        "confirm": __confirm,
        "exec": __exec,
        "__str__": __str__,
    }
    if edit_roles:
        attributes["groups_allowed"] = __groups_allowed

    return create_class(f"commands.{facade_name}.remove", "RemoveCommand", parents=_parents, attributes=attributes)
