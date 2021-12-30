from .command import client as command_api
from .data import client as data_api


class Client(object):

    def __init__(self,
        token,
        host = 'localhost',
        command_port = 5123,
        data_port = 5323,
        user = 'admin',
        options_callback = None,
        message_callback = None,
        encryption_key = None
    ):
        self.command = command_api.Client(token,
            host = host,
            port = command_port,
            user = user,
            options_callback = options_callback,
            message_callback = message_callback,
            encryption_key = encryption_key
        )
        self.data = data_api.Client(token,
            host = host,
            port = data_port,
            user = user,
            encryption_key = encryption_key
        )

    @property
    def actions(self):
        return self.command.actions

    def get_action_options(self, action):
        return self.command.get_options(action)

    @property
    def data_types(self):
        return self.data.data_types

    def get_data_options(self, data_type):
        return self.data.get_options(data_type)


    def list(self, data_type, **options):
        return self.data.list(data_type, options)

    def get(self, data_type, key, **options):
        return self.data.get(data_type, key, options)

    def save(self, data_type, key, fields = None, provider = None, **options):
        return self.command.save(data_type, key,
            fields = fields,
            provider = provider,
            **options
        )

    def remove(self, data_type, key, **options):
        return self.command.remove(data_type, key, **options)

    def clear(self, data_type, **options):
        return self.command.clear(data_type, **options)


    def values(self, data_type, field_name, **options):
        return self.data.values(data_type, field_name, options)

    def count(self, data_type, field_name, **options):
        return self.data.count(data_type, field_name, options)


    def download(self, dataset_name):
        return self.data.download(dataset_name)


    def execute(self, action, **options):
        return self.command.execute(action, **options)


    def run_task(self, module_name, task_name, config = None, **options):
        return self.command.run_task(module_name, task_name,
            config = config,
            **options
        )

    def run_profile(self, module_name, profile_name, config = None, components = None, **options):
        return self.command.run_profile(module_name, profile_name,
            config = config,
            components = components,
            **options
        )

    def destroy_profile(self, module_name, profile_name, config = None, components = None, **options):
        return self.command.destroy_profile(module_name, profile_name,
            config = config,
            components = components,
            **options
        )


    def run_imports(self, names = None, tags = None, **options):
        return self.command.run_imports(names, tags, **options)

    def run_calculations(self, names = None, tags = None, **options):
        return self.command.run_calculations(names, tags, **options)


    def __getattr__(self, attr):
        def enclosure(**options):
            return self.execute(attr.replace('__', '/'), **options)
        return enclosure
