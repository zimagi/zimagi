import os

from django.utils.module_loading import import_string


class IndexerComponentMixin:
    def load_component(self, profile, name):
        component_class = f"components.{name}.ProfileComponent"
        return import_string(component_class)(name, profile)

    def load_components(self, profile):
        components = {}
        for component_dir in self.get_module_dirs("components"):
            for type in os.listdir(component_dir):
                if type[0] != "_" and type.endswith(".py"):
                    name = type.replace(".py", "")

                    if name != "config":
                        instance = self.load_component(profile, name)
                        priority = instance.priority()

                        if priority not in components:
                            components[priority] = [instance]
                        else:
                            components[priority].append(instance)
        return components

    def load_component_names(self, profile, filter_method=None):
        component_map = self.load_components(profile)
        component_names = []

        for priority, component_list in sorted(component_map.items()):
            for component in component_list:
                if not filter_method or getattr(component, filter_method)():
                    component_names.append(component.name)

        return component_names
