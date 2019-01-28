from django.conf import settings

from systems.command import providers

import threading
import pathlib
import copy


class StorageResult(object):

    def __init__(self, type, config,
        name = None,
        fs_name = None,
        region = None,
        zone = None,
        remote_host = None,
        remote_path = None,
        mount_options = None
    ):
        self.type = type
        self.config = copy.deepcopy(config)
        self.name = name
        self.fs_name = fs_name
        self.region = region
        self.zone = zone
        self.remote_host = remote_host
        self.remote_path = remote_path
        self.mount_options = mount_options

    def __str__(self):
        return "[{}:{}:{}]> {}/{} ({}:{})".format(
            self.type,
            self.region,
            self.zone,
            self.fs_name,
            self.name,
            self.remote_host,
            self.remote_path         
        )


class BaseStorageProvider(providers.BaseCommandProvider):

    def __init__(self, name, command, storage = None):
        super().__init__(name, command)

        self.storage = storage
        self.thread_lock = threading.Lock()

        self.provider_type = 'storage'
        self.provider_options = settings.STORAGE_PROVIDERS


    def create_storage_mounts(self, config, complete_callback = None):
        self.config = config
        
        self.provider_config()
        self.validate()

        def storage_callback(arg):
            storage = StorageResult(self.name, self.config)

            for key, value in self.config.items():
                if hasattr(storage, key) and key not in ('type', 'config'):
                    setattr(storage, key, value)

            return storage

        self.initialize_provider_filesystem()

        return self.command.run_list(
            self.config.pop('list', [0]), 
            self.create_provider_storage_mount,
            state_callback = storage_callback,
            complete_callback = complete_callback
        )

    def initialize_provider_filesystem(self):
        # Override in subclass
        pass

    def create_provider_storage_mount(self, index, storage):
        # Override in subclass
        pass


    def destroy_storage_mount(self, abort = False):
        if not self.storage:
            self.command.error("Destroying storage mount requires a valid storage instance given to provider on initialization")
        try:
            self.destroy_provider_storage_mount()
        
        except Exception as e:
            if abort:
                raise e
            else:
                self.command.warning(str(e))

    def destroy_provider_storage_mount(self):
        # Override in subclass
        pass
