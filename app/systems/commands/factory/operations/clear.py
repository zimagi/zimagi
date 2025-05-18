from utility.data import ensure_list
from utility.python import create_class

from ..helpers import get_facade


def ClearCommand(parents, base_name, facade_name, edit_roles=None):
    _parents = ensure_list(parents)
    _facade_name = get_facade(facade_name)

    def __get_priority(self):
        return 25

    def __get_run_background(self):
        return False

    def __groups_allowed(self):
        from settings.roles import Roles

        return [Roles.admin] + ensure_list(edit_roles)

    def __parse(self, add_api_fields=False):
        facade = getattr(self, _facade_name)
        self.parse_search(True)
        self.parse_force()
        self.parse_scope(facade)

    def __confirm(self):
        return True

    def __exec(self):
        facade = getattr(self, _facade_name)
        self.set_scope(facade, True)

        instances = self.search_instances(facade, self.search_queries, self.search_join)

        def remove(instance):
            self.remove_instance(facade, getattr(instance, facade.key()))

        self.run_list(instances, remove)
        self.success(f"Successfully cleared all {facade.plural}")

    def __str__(self):
        return f"Clear <{base_name}>"

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

    return create_class(f"commands.{facade_name}.clear", "ClearCommand", parents=_parents, attributes=attributes)
