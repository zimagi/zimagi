import itertools
import string
import random
import pickle
import codecs
import re
import json
import hashlib


class Collection(object):
    def __init__(self, **attributes):
        for key, value in attributes.items():
            setattr(self, key, value)

    def __getattr__(self, name):
        if name not in self.__dict__:
            return None

    def __str__(self):
        return json.dumps(self.__dict__)

    def __repr__(self):
        return self.__str__()


def ensure_list(data, preserve_null = False):
    if preserve_null and data is None:
        return None
    return list(data) if isinstance(data, (list, tuple)) else [data]


def intersection(data1, data2, ignore_if_empty = False):
    if ignore_if_empty and not data2:
        return data1
    return list(set(ensure_list(data1)) & set(ensure_list(data2)))


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

def sorted_keys(data, key = None, reverse = False):
    if key:
        return sorted(data, key = lambda x: (data[x][key]), reverse = reverse)
    else:
        return sorted(data, key = lambda x: (data[x]), reverse = reverse)


def env_value(data):
    if isinstance(data, dict):
        for key, value in data.items():
            data[key] = env_value(value)
    elif isinstance(data, (list, tuple)):
        values = []
        for value in data:
            values.append(env_value(value))
        data = ",".join(values)
    else:
        data = str(data)
    return data

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
            value = list(value)
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

def get_dict_combinations(data):
    fields = sorted(data)
    combos = []
    for combo_values in itertools.product(*(ensure_list(data[name]) for name in fields)):
        combo_data = {}
        for index, field in enumerate(fields):
            combo_data[field] = combo_values[index]
        combos.append(combo_data)
    return combos


def normalize_index(index):
    try:
        return int(index)
    except ValueError:
        return index


def number(data):
    try:
        return int(data)
    except ValueError:
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


def create_token(length = 32):
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    return 't' + ''.join(random.SystemRandom().choice(chars) for _ in range(length))


def serialized_token():
    return '<<serialized>>'

def serialize(data):
    return codecs.encode(pickle.dumps(data), "base64").decode().replace("\n", '')

def unserialize(data):
    if data is None:
        return data
    return pickle.loads(codecs.decode(data.encode(), "base64"))


def get_identifier(values):
    values = [ str(item) for item in values ]
    return hashlib.sha256("-".join(values).encode()).hexdigest()
