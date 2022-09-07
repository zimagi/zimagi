from utility.data import ensure_list
from utility.python import create_class
from ..helpers import *


def ListCommand(parents, base_name, facade_name,
    view_roles = None
):
    _parents = ensure_list(parents)
    _facade_name = get_facade(facade_name)
    _order_field = get_joined_value(base_name, 'order')
    _limit_field = get_joined_value(base_name, 'limit')


    def __get_priority(self):
        return 5

    def __groups_allowed(self):
        from settings.roles import Roles
        return [ Roles.admin ] + ensure_list(view_roles)

    def __get_epilog(self):
        facade = getattr(self, _facade_name)
        variable = "{}_list_fields".format(facade.name)
        fields = [ x.name for x in reversed(facade.meta.get_fields()) ]

        return 'field display config: {}\n\n> {} fields: {}'.format(
            self.header_color(variable),
            facade.name,
            self.notice_color(", ".join(fields))
        )


    def __parse(self):
        getattr(self, "parse_{}".format(_order_field))('--order')
        getattr(self, "parse_{}".format(_limit_field))('--limit')

        self.parse_search(True)
        parse_field_names(self)


    def __exec(self):
        filters = {}
        facade = getattr(self, _facade_name)
        queries = self.search_queries
        if queries:
            instances = self.search_instances(facade, queries, self.search_join)
            filters["{}__in".format(facade.pk)] = [ getattr(x, facade.pk) for x in instances ]

        count = facade.count(**filters)

        order_by = getattr(self, _order_field, None)
        if order_by:
            facade.set_order(order_by)

        limit = getattr(self, _limit_field, None)
        if limit:
            facade.set_limit(limit)

        data = self.render_list(
            facade,
            filters = filters,
            allowed_fields = get_field_names(self)
        )
        if data:
            self.info('')
            self.data(" {} results".format(facade.name.capitalize()), count, 'total')
            if limit:
                self.data(' Showing', min(len(data) - 1, limit), 'count')
            self.table(data, 'results')
        else:
            self.error('No results', silent = True)


    def __str__(self):
        return "List <{}>".format(base_name)


    attributes = {
        '_resource': facade_name,
        'get_priority': __get_priority,
        'get_epilog': __get_epilog,
        'parse': __parse,
        'exec': __exec,
        '__str__': __str__
    }
    if view_roles:
        attributes['groups_allowed'] = __groups_allowed


    return create_class(
        "commands.{}.list".format(facade_name),
        'ListCommand',
        parents = _parents,
        attributes = attributes
    )
