import types
import importlib
import logging
import re
import sys

from .data import dump_json

logger = logging.getLogger(__name__)


def create_module(module_path):
    module = types.ModuleType(module_path)
    sys.modules[module_path] = module
    return module


def get_module(module_path):
    try:
        module = importlib.import_module(module_path)
    except ModuleNotFoundError:
        module = create_module(module_path)

    return {"module": module, "path": module_path}


def create_class(module_path, name, parents=None, attributes=None):
    if parents is None:
        parents = []
    if attributes is None:
        attributes = {}

    module_info = get_module(module_path)

    klass = type(name, tuple(parents), attributes)
    klass.__module__ = module_info["path"]
    setattr(module_info["module"], name, klass)
    return klass


class PythonValueInvalid(Exception):
    pass


class PythonParser:
    variable_pattern = r"^\@\{?([\_a-zA-Z0-9][\_\-a-zA-Z0-9]+\.[\_\-a-zA-Z0-9]+)\}?$"
    variable_value_pattern = r"(?<!\@)\@\>?\{?([\_a-zA-Z0-9][\_\-a-zA-Z0-9]+\.[\_\-a-zA-Z0-9]+)\}?"

    def __init__(self, modules):
        self.modules = modules

    def parse(self, value):
        if not isinstance(value, str):
            return value

        if re.search(self.variable_pattern, value):
            value = self.parse_variable(value)
        else:
            for ref_match in re.finditer(self.variable_value_pattern, value):
                variable_value = self.parse_variable(f"@{ref_match.group(1)}")
                if isinstance(variable_value, (list, tuple)):
                    variable_value = ",".join(variable_value)
                elif isinstance(variable_value, dict):
                    variable_value = dump_json(variable_value)

                if variable_value:
                    value = value.replace(ref_match.group(0), str(variable_value)).strip()
        return value

    def parse_variable(self, value):
        config_match = re.search(self.variable_pattern, value)
        if config_match:
            lookup = config_match.group(1).split(".")
            attribute = lookup.pop()
            lookup_name = ".".join(lookup)

            for name, lookup_module in self.modules.items():
                if name == lookup_name and hasattr(lookup_module, attribute):
                    return getattr(lookup_module, attribute)
            try:
                module = importlib.import_module(lookup_name)
                return getattr(module, attribute)

            except Exception as e:
                logger.error("Module attribute import failed: {}.{}: {}".format(".".join(lookup), attribute, e))

        # Not found, raise alarm bells!!
        raise PythonValueInvalid(f"No Python module/attribute combination for lookup: {value}")
