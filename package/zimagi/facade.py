from .command import client as command_api
from .data import client as data_api

from . import settings


class Client(object):

    def __init__(self,
        host = settings.DEFAULT_HOST,
        command_port = settings.DEFAULT_COMMAND_PORT,
        data_port = settings.DEFAULT_DATA_PORT,
        verify_cert = settings.DEFAULT_VERIFY_CERT,
        user = settings.DEFAULT_USER,
        token = settings.DEFAULT_TOKEN,
        encryption_key = None,
        options_callback = None,
        message_callback = None
    ):
        self.command = command_api.Client(
            host = host,
            port = command_port,
            verify_cert = verify_cert,
            user = user,
            token = token,
            encryption_key = encryption_key,
            options_callback = options_callback,
            message_callback = message_callback
        )
        self.data = data_api.Client(
            host = host,
            port = data_port,
            verify_cert = verify_cert,
            user = user,
            token = token,
            encryption_key = encryption_key,
            options_callback = options_callback
        )

    @property
    def actions(self):
        return self.command.actions

    def get_action_options(self, action):
        return self.command.get_options(action)

    @property
    def data_types(self):
        return list(self.command.data_types.keys())

    def get_data_options(self, data_type):
        return self.data.get_options(data_type)


    def list(self, data_type, **options):
        return self.data.list(data_type, options)

    def json(self, data_type, **options):
        return self.data.json(data_type, options)

    def csv(self, data_type, **options):
        return self.data.csv(data_type, options)

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


    def extend(self, remote, reference, provider = None, **fields):
        return self.command.extend(remote, reference, provider = provider, **fields)


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
