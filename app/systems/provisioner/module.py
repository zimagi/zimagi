
class ModuleMixin(object):

    def get_module(self, name):
        facade = self.command.facade(self.command._module)
        return self.command.get_instance(facade, name, required = False)

    def ensure_module(self, name, config):
        provider = config.pop('provider', None)
        if provider is None:
            self.command.error("Module {} requires 'provider' field".format(name))

        self.command.exec_local('module save', {
            'module_provider_name': provider,
            'module_name': name,
            'module_fields': config
        })

    def describe_module(self, module):
        return { 'provider': module.type }

    def destroy_module(self, name, config):
        self.command.exec_local('module rm', {
            'module_name': name,
            'force': True
        })
