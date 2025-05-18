import copy
import importlib
import inspect
import logging
import sys
import types

from django.conf import settings
from utility.data import deep_merge, ensure_list
from utility.python import PythonParser

logger = logging.getLogger(__name__)


class PluginNotExistsError(Exception):
    pass


class SpecNotFound(Exception):
    pass


def format_class_name(name, suffix=""):
    return "".join([component.title() for component in name.split("_")]) + suffix


def get_plugin_name(name, spec=None):
    if spec and "class" in spec:
        return spec["class"]
    return format_class_name(name.split(".")[-1])


def get_module_name(key, name, provider=None):
    if key == "plugin_mixins":
        module_path = f"plugins.mixins.{name}"
    elif key == "plugin":
        if provider:
            module_path = f"plugins.{name}.{provider}"
        else:
            module_path = f"plugins.{name}"
    else:
        raise SpecNotFound(f"Key {key} is not supported for plugin: {name} ({provider})")
    return module_path


class BaseGenerator:
    def __init__(self, key, name, ensure_exists=False):
        self.parser = PythonParser({"settings": settings})
        self.key = key
        self.name = name
        self.name_list = self.name.split(".")

        self.full_spec = settings.MANAGER.get_spec()
        self.plugin_spec = self.full_spec[self.key]
        self._spec = None
        self.parents = []

        self.ensure_exists = ensure_exists
        self.attributes = {}

    @property
    def spec(self):
        if self._spec is None:
            self._spec = self.get_spec()
        return self._spec

    def get_spec(self):
        # Override in sub class
        return {}

    @property
    def base_class_name(self):
        # Override in sub class
        return ""

    @property
    def dynamic_class_name(self):
        return f"{self.base_class_name}Dynamic"

    @property
    def klass(self):
        if getattr(self.module, self.base_class_name, None):
            klass = getattr(self.module, self.base_class_name)
        else:
            klass = getattr(self.module, self.dynamic_class_name, None)
            if klass and self.ensure_exists:
                klass = self.create_overlay(klass)

        return klass

    def get_module(self, name, provider=None):
        module_path = get_module_name(self.key, name, provider)
        try:
            module = importlib.import_module(module_path)
        except ModuleNotFoundError:
            module = types.ModuleType(module_path)
            sys.modules[module_path] = module

        return {"module": module, "module_path": module_path}

    def init(self):
        self.attributes["meta"] = {
            "requirement": self.spec.get("requirement", {}),
            "option": self.spec.get("option", {}),
            "interface": self.spec.get("interface", {}),
        }

        if getattr(self, "base_class", None):
            self.parents = [self.base_class]

        elif inspect.isclass(self.spec.get("base", None)):
            self.parents = [self.spec["base"]]

        else:
            self.parents = [self.get_parent()]

        meta_attributes = copy.deepcopy(getattr(self.parents[0], "meta", {}))

        if "mixins" in self.spec:
            for mixin in ensure_list(self.spec["mixins"]):
                provider_mixin = ProviderMixin(mixin)
                meta_attributes = deep_merge(meta_attributes, getattr(provider_mixin, "meta", {}))
                self.parents.append(provider_mixin)

        self.attributes["meta"] = deep_merge(meta_attributes, self.attributes["meta"])
        for name in list(self.attributes["meta"]["option"].keys()):
            info = self.attributes["meta"]["option"][name]
            if info is None:
                self.attributes["meta"]["option"].pop(name)

            self.attributes["meta"]["requirement"].pop(name, None)

    def get_parent(self):
        # Override in sub class
        return None

    def create(self):
        self.init()

        parent_classes = copy.deepcopy(self.parents)
        parent_classes.reverse()

        self.create_process()

        plugin = type(self.dynamic_class_name, tuple(parent_classes), self.attributes)
        plugin.__module__ = self.module_path
        setattr(self.module, self.dynamic_class_name, plugin)

        for parent in self.parents:
            parent.generate(plugin, self)  # Allow parents to initialize class

        if self.ensure_exists:
            return self.create_overlay(plugin)
        return plugin

    def create_process(self):
        # Override in sub class if needed
        pass

    def create_overlay(self, plugin):
        if getattr(self.module, self.base_class_name, None):
            return getattr(self.module, self.base_class_name)

        overlay_plugin = type(self.base_class_name, (plugin,), {})
        overlay_plugin.__module__ = self.module_path
        setattr(self.module, self.base_class_name, overlay_plugin)
        return overlay_plugin

    def parse_values(self, item):
        if isinstance(item, (list, tuple)):
            for index, element in enumerate(item):
                item[index] = self.parse_values(element)
        elif isinstance(item, dict):
            for name, element in item.items():
                item[name] = self.parse_values(element)
        elif isinstance(item, str):
            item = self.parser.parse(item)
        return item


class ProviderMixinGenerator(BaseGenerator):
    def __init__(self, plugin_name):
        super().__init__("plugin_mixins", plugin_name)
        module_info = self.get_module(self.name)
        self.module = module_info["module"]
        self.module_path = module_info["module_path"]

    def get_spec(self):
        spec = self.plugin_spec.get(self.name, {})
        if not spec:
            raise SpecNotFound(f"Plugin specification does not exist for {self.name}")
        return self.parse_values(spec)

    @property
    def base_class_name(self):
        return get_plugin_name(self.name, self.spec)

    def get_parent(self):
        if "base" not in self.spec or self.spec["base"] == "base":
            from systems.plugins.base import BasePluginMixin

            return BasePluginMixin
        return ProviderMixin(self.spec["base"])


class PluginGenerator(BaseGenerator):
    def __init__(self, plugin_name, ensure_exists=False):
        super().__init__("plugin", plugin_name, ensure_exists=ensure_exists)
        self.plugin = self.name_list[0]
        self.subtype = self.name_list[-1] if len(self.name_list) > 1 else None
        self.subtypes = None

        module_info = self.get_module(self.plugin, "base")
        self.module = module_info["module"]
        self.module_path = module_info["module_path"]

    def get_spec(self):
        spec = self.plugin_spec.get(self.plugin, {})

        if self.subtype and "subtypes" in spec:
            self.subtypes = spec["subtypes"]
            spec = spec["subtypes"].get(self.subtype, {})

        if not spec:
            raise SpecNotFound(f"Plugin specification does not exist for {self.name}")
        return self.parse_values(spec)

    @property
    def base_class_name(self):
        if self.subtype:
            return format_class_name(self.subtype, "BaseProvider")
        return "BaseProvider"

    def get_parent(self):
        if self.subtypes and self.spec.get("base", None) and self.spec["base"] in self.subtypes.keys():
            parent = BasePlugin("{}.{}".format(self.plugin, self.spec["base"]))
        else:
            if "base" not in self.spec:
                self.spec["base"] = "base"

            module_path = get_module_name(self.key, self.spec["base"])
            try:
                parent = getattr(importlib.import_module(module_path), "BasePlugin")
            except Exception as e:
                raise PluginNotExistsError("Base plugin {} does not exist: {}".format(self.spec["base"], e))

        return parent

    def create_process(self):
        for method, info in self.attributes["meta"]["interface"].items():

            def interface_method(self, *args, **kwargs):
                return None

            interface_method.__name__ = method
            self.attributes[method] = interface_method


class ProviderGenerator(PluginGenerator):
    def __init__(self, plugin_name, provider_name, ensure_exists=False):
        super().__init__(plugin_name, ensure_exists=ensure_exists)
        self.provider = provider_name

        module_info = self.get_module(self.plugin, self.provider)
        self.module = module_info["module"]
        self.module_path = module_info["module_path"]

    def get_spec(self):
        spec = self.plugin_spec.get(self.plugin, {}).get("providers", {}).get(self.provider, {})
        if self.subtype and "subtypes" in spec:
            self.subtypes = spec["subtypes"]
            spec = spec["subtypes"].get(self.subtype, {})
        if spec is None:
            spec = {}
        return self.parse_values(spec)

    @property
    def base_class_name(self):
        if self.subtype:
            return format_class_name(self.subtype, "Provider")
        return "Provider"

    def get_parent(self):
        base = None
        if self.spec.get("base", None):
            base = self.spec["base"]

        if self.subtype:
            plugin = f"{self.plugin}.{self.subtype}"
            if not base:
                spec = self.plugin_spec.get(self.plugin, {}).get("providers", {}).get(self.provider, {})
                base = spec.get("base", None)
        else:
            plugin = self.plugin

        if base:
            parent = BaseProvider(plugin, base)
        else:
            parent = BasePlugin(plugin)

        return parent

    def create_process(self):
        pass


def BasePlugin(plugin_name, ensure_exists=False):
    plugin = PluginGenerator(plugin_name, ensure_exists=ensure_exists)
    klass = plugin.klass
    if klass:
        return klass

    if not plugin.spec:
        raise PluginNotExistsError(f"Plugin {plugin.base_class_name} does not exist yet")

    return plugin.create()


def ProviderMixin(plugin_mixin_name):
    mixin = ProviderMixinGenerator(plugin_mixin_name)
    klass = mixin.klass
    if klass:
        return klass

    if not mixin.spec:
        raise PluginNotExistsError(f"Plugin provider mixin {mixin.base_class_name} does not exist yet")

    return mixin.create()


def BaseProvider(plugin_name, provider_name, ensure_exists=False):
    provider = ProviderGenerator(plugin_name, provider_name, ensure_exists=ensure_exists)
    klass = provider.klass
    if klass:
        return klass

    return provider.create()


def display_plugin_info(klass, prefix="", display_function=logger.info):
    display_function(f"{prefix}{klass.__name__}")
    for parent in klass.__bases__:
        display_plugin_info(parent, f"{prefix}  << ", display_function)

    display_function(f"{prefix} properties:")
    for attribute in dir(klass):
        if not attribute.startswith("__") and not callable(getattr(klass, attribute)):
            display_function(f"{prefix}  ->  {attribute}")

    display_function(f"{prefix} methods:")
    for attribute in dir(klass):
        if not attribute.startswith("__") and callable(getattr(klass, attribute)):
            display_function(f"{prefix}  **  {attribute}")
