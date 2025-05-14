import urllib

from .. import exceptions, utility
from . import schema


def get_value(item, key):
    value = item.get(key)
    return value


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


def unescape_key(string):
    if string.startswith("__") and string.lstrip("_") in ("type", "meta"):
        return string[1:]
    return string


class CommandParseError(Exception):
    pass


class ZimagiJSONCodec:
    media_types = ["application/vnd.zimagi+json", "application/x-zimagi+json"]

    def decode(self, bytestring, **options):
        base_url = options.get("base_url")

        try:
            data = utility.load_json(bytestring.decode("utf-8"))
        except ValueError as exc:
            raise exceptions.ParseError(f"Malformed JSON. {exc}")

        document = self._convert_to_schema(data, base_url)

        if not (isinstance(document, schema.Root) or isinstance(document, schema.Error)):
            raise CommandParseError("Top level node should be a root or error.")

        return document

    def _convert_to_schema(self, data, base_url=None):
        if isinstance(data, dict) and data.get("_type") == "root":
            meta = get_dict(data, "_meta")
            url = urllib.parse.urljoin(base_url, get_string(meta, "url"))
            return schema.Root(
                commands=self._get_document_content(data, base_url=url),
                url=url,
                title=get_string(meta, "title"),
                description=get_string(meta, "description"),
                media_type="application/vnd.zimagi+json",
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
                epilog=get_string(data, "epilog"),
                priority=get_number(meta, "priority", 1),
                resource=get_string(meta, "resource"),
            )
        elif isinstance(data, dict) and data.get("_type") == "action":
            return schema.Action(
                url=urllib.parse.urljoin(base_url, get_string(data, "url")),
                name=get_string(data, "name"),
                overview=get_string(data, "overview"),
                description=get_string(data, "description"),
                epilog=get_string(data, "epilog"),
                priority=get_number(data, "priority", 1),
                resource=get_string(data, "resource"),
                confirm=get_bool(data, "confirm"),
                fields=[
                    schema.Field(
                        method=get_string(item, "method"),
                        name=get_string(item, "name"),
                        type=get_string(item, "type"),
                        argument=get_string(item, "argument"),
                        config=get_string(item, "config"),
                        description=get_string(item, "description"),
                        value_label=get_string(item, "value_label"),
                        system=get_bool(item, "system"),
                        required=get_bool(item, "required"),
                        default=get_value(item, "default"),
                        choices=get_list(item, "choices"),
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
