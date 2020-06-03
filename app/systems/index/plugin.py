import os
import importlib


class ProviderNotFoundError(Exception):
    pass


class IndexerPluginMixin(object):

    def __init__(self):
        self.plugin_directories = self.get_module_dirs('plugins')
        self.plugin_providers = {}
        super().__init__()


    def load_plugin_providers(self, name, spec, base_provider_class):
        self.plugin_providers[name] = {
            'base': base_provider_class,
            'providers': {}
        }
        for plugin_dir in self.plugin_directories:
            plugin_dir = os.path.join(plugin_dir, name)
            if os.path.isdir(plugin_dir):
                for provider in os.listdir(plugin_dir):
                    if provider[0] != '_' and provider != 'base.py' and provider.endswith('.py'):
                        provider = provider.strip('.py')
                        module = importlib.import_module("plugins.{}.{}".format(name, provider))

                        provider_class = getattr(module, 'Provider', None)
                        if provider_class is None:
                            raise ProviderNotFoundError("Plugin {} provider {} (Provider class) not defined".format(name, provider))

                        self.plugin_providers[name]['providers'][provider] = provider_class


    def get_plugin_base(self, name):
        return self.plugin_providers[name]['base']

    def get_plugin_providers(self, name, include_system = False):
        providers = {}
        for provider, provider_class in self.plugin_providers[name]['providers'].items():
            if include_system or not provider.startswith('sys_'):
                providers[provider] = provider_class
        return providers
