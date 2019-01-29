import string
import random


def clean_dict(data):
    return {key: value for key, value in data.items() if value is not None}


def create_token():
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.SystemRandom().choice(chars) for _ in range(32))
