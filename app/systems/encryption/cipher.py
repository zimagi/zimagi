import copy
import importlib
from functools import lru_cache

import oyaml
from django.conf import settings
from utility.data import serialize
from utility.project import project_dir


class EncryptionError(Exception):
    pass


class MetaCipher(type):
    @property
    @lru_cache(maxsize=None)
    def providers(self):
        return settings.MANAGER.index.get_plugin_providers(self.plugin_type, True)

    @property
    @lru_cache(maxsize=None)
    def types(self):
        return settings.MANAGER.get_spec(self.plugin_type)

    @lru_cache(maxsize=None)
    def get_type_spec(self, type):
        spec = self.types.get(type, None)
        if not spec:
            raise EncryptionError(f"Encryption type specification {type} not found")
        return spec

    @property
    @lru_cache(maxsize=None)
    def state_names(self):
        names = []
        for type, spec in self.types.items():
            if spec.get("initialize", True):
                names.append(type)
        return names

    @lru_cache(maxsize=None)
    def get_state(self, type):
        state_cipher = self.get_state_provider(type)

        with project_dir(self.plugin_type, "keys", base_path=settings.ROOT_LIB_DIR) as file:
            config = file.load(f".{type}")
            if config:
                config = oyaml.safe_load(state_cipher.decrypt(config))
            return config

    def save_state(self, type, cipher):
        state_cipher = self.get_state_provider(type)

        with project_dir(self.plugin_type, "keys", base_path=settings.ROOT_LIB_DIR) as file:
            file.save(
                state_cipher.encrypt(oyaml.dump({**cipher.config, "provider": cipher.name})).decode("utf-8"), f".{type}"
            )

    def get_state_provider(self, type):
        return self.get_provider(type, settings.ENCRYPTION_STATE_PROVIDER, settings.ENCRYPTION_STATE_KEY, {})

    def initialize(self):
        for type, spec in self.types.items():
            if spec.get("initialize", True):
                self.run_migration(type, self.get(type), self.get_from_spec(type))

    def get(self, type, **options):
        type_id = f"{type}-{serialize(options)}" if options else type

        if type_id not in self.cipher:
            if not getattr(settings, f"ENCRYPT_{type.upper()}", True):
                self.cipher[type_id] = self.get_base(type)
            else:
                cipher = None

                if not options:
                    cipher = self.get_from_state(type)
                if not cipher:
                    cipher = self.get_from_spec(type, options)

                self.cipher[type_id] = cipher

        return self.cipher[type_id]

    def get_provider_class(self, type):
        return self.get_from_spec(type, class_only=True)

    def get_base(self, type, class_only=False):
        return self.get_provider(type, "base", None, {}, class_only=class_only)

    def get_from_spec(self, type, options=None, class_only=False):
        spec = self.get_type_spec(type)

        if not options:
            options = {}

        return self.get_provider(
            type,
            spec.get("provider", "base"),
            f"/var/local/keys/{type}.key",
            {**spec.get("options", {}), **options},
            class_only=class_only,
        )

    def get_from_state(self, type, class_only=False):
        state = self.get_state(type)
        if state is None:
            return None

        state = copy.deepcopy(state)
        return self.get_provider(
            type, state.pop("provider"), state.pop("key", None), state, initialize=False, class_only=class_only
        )

    def get_provider(self, type, name, key, options, initialize=True, class_only=False):
        base_provider = settings.MANAGER.index.get_plugin_base(self.plugin_type)
        providers = self.providers

        if name == "base":
            provider_class = base_provider
        elif name in providers.keys():
            provider_class = providers[name]
        else:
            raise EncryptionError(f"Encryption provider {name} not supported")

        if class_only:
            return provider_class
        try:
            options["type"] = type
            options["key"] = key
            return provider_class(self.plugin_type, name, options, initialize=initialize)
        except Exception as error:
            raise EncryptionError(f"Encryption provider {name} error: {error}")

    def run_migration(self, type, current_cipher, spec_cipher):
        state = self.get_state(type)

        if not state or current_cipher != spec_cipher:
            if state:
                try:
                    migration_lib = importlib.import_module(f"systems.encryption.{type}")
                    migration = migration_lib.Migration(type, old_cipher=current_cipher, new_cipher=spec_cipher)
                except ModuleNotFoundError:
                    migration = None
                except AttributeError:
                    raise EncryptionError(f"Migration class required in encryption type library: {type}")

                if migration:
                    migration.run()

            self.save_state(type, spec_cipher)


class Cipher(metaclass=MetaCipher):
    plugin_type = "encryption"
    cipher = {}
    states = {}
