def get_value(value, default):
    return value if value is not None else default


def get_facade(base_name):
    return f"_{base_name}"


def get_joined_value(*args):
    return "_".join([x for x in args if x is not None])


def parse_field_names(command):
    command.parse_variables(
        "field_names", "--fields", str, "field names to display", value_label="FIELD_NAME", tags=["fields"]
    )


def get_field_names(command):
    return command.options.get("field_names")


def parse_fields(command, fields):
    for name, info in fields.items():
        getattr(command, f"parse_{info[0]}")(*info[1:], tags=["fields"])


def get_fields(command, fields):
    data = {}
    for name, info in fields.items():
        data[name] = getattr(command, info[0])
    return data
