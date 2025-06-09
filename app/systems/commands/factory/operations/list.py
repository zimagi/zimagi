from utility.data import ensure_list
from utility.python import create_class

from ..helpers import get_facade, get_field_names, get_joined_value, parse_field_names


def ListCommand(parents, base_name, facade_name, view_roles=None):
    _parents = ensure_list(parents)
    _facade_name = get_facade(facade_name)
    _order_field = get_joined_value(base_name, "order")
    _limit_field = get_joined_value(base_name, "limit")
    _count_field = get_joined_value(base_name, "count")

    def __get_priority(self):
        return 5

    def __get_run_background(self):
        return False

    def __groups_allowed(self):
        from settings.roles import Roles

        return [Roles.admin] + ensure_list(view_roles)

    def __get_epilog(self):
        facade = getattr(self, _facade_name)
        variable = f"{facade.name}_list_fields"
        fields = [x.name for x in reversed(facade.meta.get_fields())]

        return "field display config: {}\n\n> {} fields: {}".format(
            self.header_color(variable), facade.name, self.notice_color(", ".join(fields))
        )

    def __parse(self, add_api_fields=False):
        getattr(self, f"parse_{_order_field}")("--order")
        getattr(self, f"parse_{_limit_field}")("--limit")
        getattr(self, f"parse_{_count_field}")()

        self.parse_search(True)
        parse_field_names(self)

    def __exec(self):
        filters = {}
        facade = getattr(self, _facade_name)
        queries = self.search_queries
        if queries:
            instances = self.search_instances(facade, queries, self.search_join)
            filters[f"{facade.pk}__in"] = [getattr(x, facade.pk) for x in instances]

        count_only = getattr(self, _count_field, None)

        count = facade.count(**filters)

        if not count_only:
            order_by = getattr(self, _order_field, None)
            if order_by:
                facade.set_order(order_by)

            limit = getattr(self, _limit_field, None)
            if limit:
                facade.set_limit(limit)

            data = self.render_list(facade, filters=filters, allowed_fields=get_field_names(self))

        if count_only or data:
            self.data(f" {facade.name.capitalize()} results", count, "total", system=True)
            if not count_only:
                if limit:
                    self.data(" Showing", min(len(data) - 1, limit), "count", system=True)
                self.table(data, "results")
            else:
                self.spacing(system=True)
        else:
            self.error("No results", silent=True)

    def __str__(self):
        return f"List <{base_name}>"

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

    return create_class(f"commands.{facade_name}.list", "ListCommand", parents=_parents, attributes=attributes)
