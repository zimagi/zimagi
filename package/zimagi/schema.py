from collections import OrderedDict


def _key_sorting(item):
    key, value = item
    if isinstance(value, Link):
        action_priority = {
            'get': 0,
            'post': 1
        }.get(value.action, 2)
        return (1, (value.url, action_priority))
    return (0, key)


class Field(object):

    def __init__(self, name,
        type = None,
        required = False,
        location = None,
        schema = None,
        tags = None

    ):
        self.name = name
        self.type = type
        self.required = required
        self.location = location
        self.schema = schema
        self.tags = [] if tags is None else tags


class Document(OrderedDict):

    def __init__(self,
        url = None,
        title = None,
        description = None,
        media_type = None,
        content = None
    ):
        self.url = '' if url is None else url
        self.title = '' if title is None else title
        self.description = '' if description is None else description
        self.media_type = '' if media_type is None else media_type

        super().__init__(**content)

    def __iter__(self):
        items = sorted(self.items(), key = _key_sorting)
        return iter([ key for key, value in items ])


    @property
    def data(self):
        return OrderedDict([
            (key, value) for key, value in self.items()
            if not isinstance(value, Link)
        ])

    @property
    def links(self):
        return OrderedDict([
            (key, value) for key, value in self.items()
            if isinstance(value, Link)
        ])


class Object(OrderedDict):

    def __iter__(self):
        items = sorted(self.items(), key = _key_sorting)
        return iter([ key for key, value in items ])

    @property
    def data(self):
        return OrderedDict([
            (key, value) for key, value in self.items()
            if not isinstance(value, Link)
        ])

    @property
    def links(self):
        return OrderedDict([
            (key, value) for key, value in self.items()
            if isinstance(value, Link)
        ])


class Array(list):
    pass


class Link(object):

    def __init__(self,
        url = None,
        action = None,
        encoding = None,
        title = None,
        description = None,
        resource = None,
        fields = None
    ):
        self.url = '' if url is None else url
        self.action = 'get' if not action else action
        self.encoding = 'application/x-www-form-urlencoded' if not encoding else encoding
        self.title = '' if title is None else title
        self.description = '' if description is None else description
        self.resource = '' if resource is None else resource
        self.fields = () if fields is None else tuple([
            item if isinstance(item, Field) else Field(item, required = False, location = '')
            for item in fields
        ])


class Error(OrderedDict):

    def __init__(self, title = None, content = None):
        if content is None:
            content = {}

        self.title = '' if title is None else title
        super().__init__(**content)

    def __iter__(self):
        items = sorted(self.items(), key = _key_sorting)
        return iter([ key for key, value in items ])

    def get_messages(self):
        messages = []
        for value in self.values():
            if isinstance(value, Array):
                messages += [
                    item for item in value if isinstance(item, str)
                ]
        return messages
