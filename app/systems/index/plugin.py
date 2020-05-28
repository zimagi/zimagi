from functools import lru_cache


class IndexerPluginMixin(object):

    def __init__(self):
        self.plugins = {}
        super().__init__()


    @lru_cache(maxsize = None)
    def load_plugins(self):
        self.plugins = {}
        for plugin_dir in self.get_module_dirs('plugins'):
            for type in os.listdir(plugin_dir):
                if type[0] != '_':
                    provider_dir = os.path.join(plugin_dir, type)
                    base_module = "plugins.{}".format(type)
                    base_class = "{}.base.BaseProvider".format(base_module)

                    if type not in self.plugins:
                        self.plugins[type] = {
                            'base': base_class,
                            'providers': {}
                        }
                    for name in os.listdir(provider_dir):
                        if name[0] != '_' and name != 'base.py' and name.endswith('.py'):
                            name = name.strip('.py')
                            provider_class = "{}.{}.Provider".format(base_module, name)
                            self.plugins[type]['providers'][name] = provider_class

    def provider_base(self, type):
        return self.plugins[type]['base']

    def providers(self, type, include_system = False):
        providers = {}
        for name, class_name in self.plugins[type]['providers'].items():
            if include_system or not name.startswith('sys_'):
                providers[name] = class_name
        return providers
