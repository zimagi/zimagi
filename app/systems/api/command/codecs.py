import urllib
from collections import OrderedDict

import coreschema
from systems.commands import schema
from utility.data import dump_json, load_json


def get_schema_class_ids():
    return {
        coreschema.Object: "object",
        coreschema.Array: "array",
        coreschema.Number: "number",
        coreschema.Integer: "integer",
        coreschema.String: "string",
        coreschema.Boolean: "boolean",
        coreschema.Null: "null",
        coreschema.Enum: "enum",
        coreschema.Anything: "anything",
    }


def get_id_schema_classes():
    return {value: key for key, value in get_schema_class_ids().items()}


def get_bool(item, key):
    value = item.get(key)
    if isinstance(value, bool):
        return value
    return False


def get_string(item, key):
    value = item.get(key)
    if isinstance(value, str):
        return value
    return ""


def get_number(item, key, default=None):
    value = item.get(key)
    if isinstance(value, (int, float)):
        return value
    return default


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


def escape_key(string):
    if string.startswith("_") and string.lstrip("_") in ("type", "meta"):
        return "_" + string
    return string


def unescape_key(string):
    if string.startswith("__") and string.lstrip("_") in ("type", "meta"):
        return string[1:]
    return string


class CommandParseError(Exception):
    pass


class ZimagiJSONCodec:
    format = "zimagi_json"

    media_type = "application/zimagi+json"
    media_types = ["application/zimagi+json", "application/vnd.zimagi+json"]

    def decode(self, bytestring, **options):
        base_url = options.get("base_url")

        try:
            data = load_json(bytestring.decode("utf-8"))
        except ValueError as error:
            raise CommandParseError(f"Malformed JSON. {error}")

        document = self._convert_to_schema(data, base_url)

        if not (isinstance(document, schema.Root) or isinstance(document, schema.Error)):
            raise CommandParseError("Top level node should be a root or error.")

        return document

    def encode(self, document, **options):
        indent = options.get("indent")

        if indent:
            kwargs = {"ensure_ascii": False, "indent": 4, "separators": (",", ": ")}
        else:
            kwargs = {"ensure_ascii": False, "indent": None, "separators": (",", ":")}

        data_str = dump_json(self._convert_to_data(document), **kwargs)
        if isinstance(data_str, str):
            return data_str.encode("utf-8")
        return data_str

    def _convert_to_schema(self, data, base_url=None):
        if isinstance(data, dict) and data.get("_type") == "root":
            meta = get_dict(data, "_meta")
            url = urllib.parse.urljoin(base_url, get_string(meta, "url"))
            return schema.Root(
                commands=self._get_document_content(data, base_url=url),
                url=url,
                title=get_string(meta, "title"),
                description=get_string(meta, "description"),
                media_type="application/zimagi+json",
            )
        if isinstance(data, dict) and data.get("_type") == "error":
            meta = get_dict(data, "_meta")
            return schema.Error(title=get_string(meta, "title"), content=self._get_document_content(data, base_url=base_url))
        elif isinstance(data, dict) and data.get("_type") == "router":
            meta = get_dict(data, "_meta")
            return schema.Router(
                commands=self._get_document_content(data, base_url=base_url),
                name=get_string(meta, "name"),
                overview=get_string(meta, "overview"),
                description=get_string(meta, "description"),
                priority=get_number(meta, "priority", 1),
                resource=get_string(meta, "resource"),
            )
        elif isinstance(data, dict) and data.get("_type") == "action":
            return schema.Action(
                url=urllib.parse.urljoin(base_url, get_string(data, "url")),
                method=get_string(data, "method"),
                encoding=get_string(data, "encoding"),
                name=get_string(data, "name"),
                overview=get_string(data, "overview"),
                description=get_string(data, "description"),
                priority=get_number(data, "priority", 1),
                resource=get_string(data, "resource"),
                fields=[
                    schema.Field(
                        name=get_string(item, "name"),
                        required=get_bool(item, "required"),
                        location=get_string(item, "location"),
                        schema=self._get_schema(item, "schema"),
                        tags=get_list(item, "tags"),
                    )
                    for item in get_list(data, "fields")
                    if isinstance(item, dict)
                ],
            )
        elif isinstance(data, dict):
            return schema.Object(self._get_document_content(data, base_url=base_url))
        elif isinstance(data, list):
            return schema.Array([self._convert_to_schema(item, base_url) for item in data])
        return data

    def _get_document_content(self, item, base_url=None):
        return {
            unescape_key(key): self._convert_to_schema(value, base_url)
            for key, value in item.items()
            if key not in ("_type", "_meta")
        }

    def _convert_to_data(self, node, base_url=None):
        if isinstance(node, schema.Root):
            ret = OrderedDict()
            ret["_type"] = "root"

            meta = OrderedDict()
            url = self._get_relative_url(base_url, node.url)
            if url:
                meta["url"] = url
            if node.title:
                meta["title"] = node.title
            if node.description:
                meta["description"] = node.description
            if meta:
                ret["_meta"] = meta

            ret.update([(escape_key(key), self._convert_to_data(value, base_url=url)) for key, value in node.items()])
            return ret

        elif isinstance(node, schema.Error):
            ret = OrderedDict()
            ret["_type"] = "error"

            if node.title:
                ret["_meta"] = {"title": node.title}

            ret.update([(escape_key(key), self._convert_to_data(value, base_url=base_url)) for key, value in node.items()])
            return ret

        elif isinstance(node, schema.Router):
            ret = OrderedDict(
                [(escape_key(key), self._convert_to_data(value, base_url=base_url)) for key, value in node.items()]
            )
            ret["_type"] = "router"

            meta = OrderedDict()
            if node.name:
                meta["name"] = node.name.strip()
            if node.overview:
                meta["overview"] = node.overview.strip()
            if node.description:
                meta["description"] = node.description.strip()
            if node.priority:
                meta["priority"] = node.priority
            if node.resource:
                meta["resource"] = node.resource
            if meta:
                ret["_meta"] = meta
            return ret

        elif isinstance(node, schema.Action):
            ret = OrderedDict()
            ret["_type"] = "action"
            url = self._get_relative_url(base_url, node.url)
            if url:
                ret["url"] = url
            if node.method:
                ret["method"] = node.method
            if node.encoding:
                ret["encoding"] = node.encoding
            if node.name:
                ret["name"] = node.name.strip()
            if node.overview:
                ret["overview"] = node.overview.strip()
            if node.description:
                ret["description"] = node.description.strip()
            if node.overview:
                ret["priority"] = node.priority
            if node.resource:
                ret["resource"] = node.resource
            if node.fields:
                ret["fields"] = [self._convert_to_data(field) for field in node.fields]
            return ret

        elif isinstance(node, schema.Field):
            ret = OrderedDict({"name": node.name})
            if node.required:
                ret["required"] = node.required
            if node.location:
                ret["location"] = node.location
            if node.schema:
                ret["schema"] = self._encode_schema(node.schema)
            if node.tags:
                ret["tags"] = node.tags
            return ret

        elif isinstance(node, schema.Object):
            return OrderedDict(
                [(escape_key(key), self._convert_to_data(value, base_url=base_url)) for key, value in node.items()]
            )
        elif isinstance(node, schema.Array):
            return [self._convert_to_data(value) for value in node]

        return node

    def _get_schema(self, item, key):
        schema_data = get_dict(item, key)
        if schema_data:
            return self._decode_schema(schema_data)
        return None

    def _encode_schema(self, schema):
        if hasattr(schema, "typename"):
            type_id = schema.typename
        else:
            type_id = get_schema_class_ids().get(schema.__class__, "anything")
        retval = {"_type": type_id, "title": schema.title, "description": schema.description}
        if hasattr(schema, "enum"):
            retval["enum"] = schema.enum
        return retval

    def _decode_schema(self, data):
        type_id = get_string(data, "_type")
        title = get_string(data, "title")
        description = get_string(data, "description")

        kwargs = {}
        if type_id == "enum":
            kwargs["enum"] = get_list(data, "enum")

        schema_cls = get_id_schema_classes().get(type_id, coreschema.Anything)
        return schema_cls(title=title, description=description, **kwargs)

    def _get_relative_url(self, base_url, url):
        if url == base_url:
            return ""

        base_prefix = "{}://{}".format(*urllib.parse.urlparse(base_url or "")[0:2])
        url_prefix = "{}://{}".format(*urllib.parse.urlparse(url or "")[0:2])

        if base_prefix == url_prefix and url_prefix != "://":
            return url[len(url_prefix) :]
        return url
