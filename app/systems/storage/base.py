from django.conf import settings

from systems.command import providers

import threading
import pathlib
import copy


class StorageResult(object):

    def __init__(self, type, name, network, config):
        self.type = type
        self.name = name
        self.network = network
        self.config = copy.deepcopy(config)

    def __str__(self):
        return "[{}:{}]> {}".format(
            self.type,
            self.network.name,
            self.name         
        )


class StorageMountResult(object):

    def __init__(self, subnet, firewalls, config,
        name = None,
        remote_host = None,
        remote_path = None,
        mount_options = None
    ):
        self.subnet = subnet
        self.firewalls = firewalls
        self.config = copy.deepcopy(config)
        self.name = name
        self.remote_host = remote_host
        self.remote_path = remote_path
        self.mount_options = mount_options

    def __str__(self):
        return "[{}]> {}{}".format(
            self.name,
            self.remote_host,
            self.remote_path         
        )


class BaseStorageProvider(providers.BaseCommandProvider):

    def __init__(self, name, command, filesystem = None):
        super().__init__(name, command)

        self.filesystem = filesystem
        self.thread_lock = threading.Lock()

        self.provider_type = 'storage'
        self.provider_options = settings.STORAGE_PROVIDERS


    def create_storage(self, name, network, config):
        self.config = config
        
        self.provider_config('storage')
        self.validate()

        storage = StorageResult(self.name, name, network, config)
        
        for key, value in self.config.items():
            if hasattr(storage, key) and key not in ('type', 'config', 'network'):
                setattr(storage, key, value)

        self.create_provider_storage(storage)
        return storage

    def create_provider_storage(self, storage):
        # Override in subclass
        pass

    def destroy_storage(self, abort = False):
        if not self.storage:
            self.command.error("Destroying storage requires a valid storage instance given to provider on initialization")
        try:
            self.destroy_provider_storage()
        
        except Exception as e:
            if abort:
                raise e
            else:
                self.command.warning(str(e))

    def destroy_provider_storage(self):
        # Override in subclass
        pass


    def create_mount(self, subnet, config, firewalls = []):
        self.config = config
        
        self.provider_config('mount')
        self.validate()

        mount = StorageMountResult(subnet, firewalls, config)

        for key, value in self.config.items():
            if hasattr(mount, key) and key not in ('config', 'subnet', 'firewalls'):
                setattr(mount, key, value)

        self.create_provider_storage_mount(mount)
        return mount

    def create_provider_mount(self, mount):
        # Override in subclass
        pass

    def update_mount_firewalls(self, mount, firewalls):
        if not self.storage:
            self.command.error("Updating storage mount firewalls requires a valid storage instance given to provider on initialization")
        try:
            self.update_provider_mount_firewalls(mount, firewalls)
        
        except Exception as e:
            if abort:
                raise e
            else:
                self.command.warning(str(e))

    def update_provider_mount_firewalls(self, mount, firewalls):
        # Override in subclass
        pass

    def destroy_mount(self, mount, abort = False):
        if not self.storage:
            self.command.error("Destroying storage mount requires a valid storage instance given to provider on initialization")
        try:
            self.destroy_provider_storage_mount(mount)
        
        except Exception as e:
            if abort:
                raise e
            else:
                self.command.warning(str(e))

    def destroy_provider_mount(self, mount):
        # Override in subclass
        pass
