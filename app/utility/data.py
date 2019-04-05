import string
import random
import pickle
import codecs
import re


def ensure_list(data):
    return list(data) if isinstance(data, (list, tuple)) else [data]


def deep_merge(destination, source):
    for key, value in source.items():
        if isinstance(value, dict):
            node = destination.setdefault(key, {})
            deep_merge(node, value)
        else:
            destination[key] = value

    return destination


def clean_dict(data):
    return {key: value for key, value in data.items() if value is not None}


def normalize_value(value):
    if value is not None:
        if isinstance(value, str):
            if re.match(r'^(NONE|None|none|NULL|Null|null)$', value):
                value = None
            elif re.match(r'^(TRUE|True|true)$', value):
                value = True
            elif re.match(r'^(FALSE|False|false)$', value):
                value = False
            elif re.match(r'^\d+$', value):
                value = int(value)
            elif re.match(r'^\d+\.\d+$', value):
                value = float(value)

        elif isinstance(value, (list, tuple)):
            for index, element in enumerate(value):
                value[index] = normalize_value(element)

        elif isinstance(value, dict):
            for key, element in value.items():
                value[key] = normalize_value(element)
    return value

def normalize_dict(data, process_func = None):
    normalized = {}

    for key, value in data.items():
        if process_func and callable(process_func):
            key, value = process_func(key, value)
        else:
            value = normalize_value(value)
        normalized[key] = value

    return normalized


def number(data):
    try:
        return int(data)
    except TypeError:
        return float(data)


def format_value(type, value):
    if value is not None:
        if type == 'dict':
            if isinstance(value, str):
                value = json.loads(value) if value != '' else {}

        elif type == 'list':
            if isinstance(value, str):
                value = [ x.strip() for x in value.split(',') ]
            else:
                value = list(value)

        elif type == 'bool':
            if isinstance(value, str):
                if value == '' or re.match(r'^(false|no)$', value, re.IGNORECASE):
                    value = False
                else:
                    value = True
            else:
                value = bool(value)

        elif type == 'int':
            value = int(value)

        elif type == 'float':
            value = float(value)

    return value


def create_token():
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.SystemRandom().choice(chars) for _ in range(32))


def serialize(data):
    return codecs.encode(pickle.dumps(data), "base64").decode()

def unserialize(data):
    if data is None:
        return data
    return pickle.loads(codecs.decode(data.encode(), "base64"))
