from .. import exceptions, utility
from . import schema

import urllib
import coreschema


def get_schema_class_ids():
    return {
        coreschema.Object: 'object',
        coreschema.Array: 'array',
        coreschema.Number: 'number',
        coreschema.Integer: 'integer',
        coreschema.String: 'string',
        coreschema.Boolean: 'boolean',
        coreschema.Null: 'null',
        coreschema.Enum: 'enum',
        coreschema.Anything: 'anything'
    }

def get_id_schema_classes():
    return {
        value: key
        for key, value
        in get_schema_class_ids().items()
    }


def get_bool(item, key):
    value = item.get(key)
    if isinstance(value, bool):
        return value
    return False

def get_string(item, key):
    value = item.get(key)
    if isinstance(value, str):
        return value
    return ''

def get_list(item, key):
    value = item.get(key)
    if isinstance(value, list):
        return value
    return []

def get_dict(item, key):
    value = item.get(key)
    if isinstance(value, dict):
        return value
    return {}


def unescape_key(string):
    if string.startswith('__') and string.lstrip('_') in ('type', 'meta'):
        return string[1:]
    return string


class ZimagiJSONCodec(object):

    media_types = ['application/zimagi+json', 'application/vnd.zimagi+json']


    def decode(self, bytestring, **options):
        base_url = options.get('base_url')

        try:
            data = utility.load_json(bytestring.decode('utf-8'))
        except ValueError as exc:
            raise exceptions.ParseError("Malformed JSON. {}".format(exc))

        document = self._convert_to_document(data, base_url)
        if isinstance(document, schema.Object):
            document = schema.Document(content = dict(document))

        elif not (isinstance(document, schema.Document) or isinstance(document, schema.Error)):
            raise exceptions.ParseError("Top level node should be a document or error.")

        return document


    def _convert_to_document(self, data, base_url = None):
        if isinstance(data, dict) and data.get('_type') == 'document':
            meta = get_dict(data, '_meta')
            url = urllib.parse.urljoin(base_url, get_string(meta, 'url'))
            return schema.Document(
                url = url,
                title = get_string(meta, 'title'),
                description = get_string(meta, 'description'),
                media_type = 'application/zimagi+json',
                content = self._get_document_content(data, base_url = url)
            )
        if isinstance(data, dict) and data.get('_type') == 'error':
            meta = get_dict(data, '_meta')
            return schema.Error(
                title = get_string(meta, 'title'),
                content = self._get_document_content(data, base_url = base_url)
            )
        elif isinstance(data, dict) and data.get('_type') == 'link':
            return schema.Link(
                url = urllib.parse.urljoin(base_url, get_string(data, 'url')),
                action = get_string(data, 'action'),
                encoding = get_string(data, 'encoding'),
                title = get_string(data, 'title'),
                description = get_string(data, 'description'),
                resource = get_string(data, 'resource'),
                fields = [
                    schema.Field(
                        name = get_string(item, 'name'),
                        required = get_bool(item, 'required'),
                        location = get_string(item, 'location'),
                        schema = self._get_schema(item, 'schema'),
                        tags = get_list(item, 'tags')
                    )
                    for item in get_list(data, 'fields') if isinstance(item, dict)
                ]
            )
        elif isinstance(data, dict):
            return schema.Object(
                self._get_document_content(data, base_url = base_url)
            )
        elif isinstance(data, list):
            return schema.Array([
                self._convert_to_document(item, base_url) for item in data
            ])
        return data

    def _get_document_content(self, item, base_url = None):
        return {
            unescape_key(key): self._convert_to_document(value, base_url)
            for key, value in item.items()
            if key not in ('_type', '_meta')
        }


    def _get_schema(self, item, key):
        schema_data = get_dict(item, key)
        if schema_data:
            return self._decode_schema(schema_data)
        return None

    def _decode_schema(self, data):
        type_id = get_string(data, '_type')
        title = get_string(data, 'title')
        description = get_string(data, 'description')

        kwargs = {}
        if type_id == 'enum':
            kwargs['enum'] = get_list(data, 'enum')

        schema_cls = get_id_schema_classes().get(type_id, coreschema.Anything)
        return schema_cls(title = title, description = description, **kwargs)
