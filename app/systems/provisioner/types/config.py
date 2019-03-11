from utility import data


class ConfigMixin(object):

    def ensure_config(self, name, value):
        self.command.exec_local('config save', {
            'config_name': name,
            'config_value_type': type(value).__name__,
            'config_value': value
        })

    def destroy_config(self, name, value):
        self.command.exec_local('config rm', {
            'config_name': name
        })
