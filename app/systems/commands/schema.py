from collections import OrderedDict


def _key_sorting(item):
    key, value = item
    if isinstance(value, Action):
        action_priority = {"get": 0, "post": 1}.get(value.action, 2)
        return (1, (value.url, action_priority))
    return (0, key)


class SortedItemsMixin:
    def __iter__(self):
        items = sorted(self.items(), key=_key_sorting)
        return iter([key for key, value in items])


class CommandIndexMixin(SortedItemsMixin):
    @property
    def data(self):
        return OrderedDict([(key, value) for key, value in self.items() if not isinstance(value, (Router, Action))])

    @property
    def routers(self):
        return OrderedDict([(key, value) for key, value in self.items() if isinstance(value, Router)])

    @property
    def actions(self):
        return OrderedDict([(key, value) for key, value in self.items() if isinstance(value, Action)])


class Root(CommandIndexMixin, OrderedDict):

    def __init__(self, commands=None, url=None, title=None, description=None, media_type=None):
        self.url = "" if url is None else url
        self.title = "" if title is None else title
        self.description = "" if description is None else description
        self.media_type = "" if media_type is None else media_type

        if commands is None:
            commands = {}

        super().__init__(**commands)


class Router(CommandIndexMixin, OrderedDict):

    def __init__(
        self,
        commands=None,
        name=None,
        overview=None,
        description=None,
        priority=None,
        resource=None,
    ):
        self.name = "" if name is None else name
        self.overview = "" if overview is None else overview
        self.description = "" if description is None else description
        self.priority = 1 if priority is None else priority
        self.resource = "" if resource is None else resource

        if commands is None:
            commands = {}

        super().__init__(**commands)


class Action:

    def __init__(
        self,
        url=None,
        method=None,
        encoding=None,
        name=None,
        overview=None,
        description=None,
        priority=None,
        resource=None,
        fields=None,
    ):
        self.url = "" if url is None else url
        self.method = "get" if not method else method
        self.encoding = "application/x-www-form-urlencoded" if not encoding else encoding
        self.name = "" if name is None else name
        self.overview = "" if overview is None else overview
        self.description = "" if description is None else description
        self.priority = 1 if priority is None else priority
        self.resource = "" if resource is None else resource
        self.fields = (
            ()
            if fields is None
            else tuple([item if isinstance(item, Field) else Field(item, required=False, location="") for item in fields])
        )


class Field:

    def __init__(self, name, type=None, required=False, secret=False, system=False, location=None, schema=None, tags=None):
        self.name = name
        self.type = type
        self.required = required
        self.secret = secret
        self.system = system
        self.location = location
        self.schema = schema
        self.tags = [] if tags is None else tags


class Error(SortedItemsMixin, OrderedDict):

    def __init__(self, title=None, content=None):
        if content is None:
            content = {}

        self.title = "" if title is None else title
        super().__init__(**content)

    def get_messages(self):
        messages = []
        for value in self.values():
            if isinstance(value, Array):
                messages += [item for item in value if isinstance(item, str)]
        return messages


class Object(SortedItemsMixin, OrderedDict):

    def __init__(self, items=None):
        if items is None:
            items = {}

        super().__init__(**items)


class Array(list):
    pass
