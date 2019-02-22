import string
import random
import pickle
import codecs


def clean_dict(data):
    return {key: value for key, value in data.items() if value is not None}

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


def number(data):
    try:
        return int(data)
    except TypeError:
        return float(data)


def create_token():
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.SystemRandom().choice(chars) for _ in range(32))


def serialize(data):
    return codecs.encode(pickle.dumps(data), "base64").decode()

def unserialize(data):
    if data is None:
        return data
    return pickle.loads(codecs.decode(data.encode(), "base64"))
