
def clean_dict(data):
    return {key: value for key, value in data.items() if value is not None}