from functools import lru_cache

from django.conf import settings
from utility.data import serialize


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

    def get(self, type, **options):
        type_id = f"{type}-{serialize(options)}" if options else type

        if type_id not in self.cipher:
            if not getattr(settings, f"ENCRYPT_{type.upper()}", True):
                self.cipher[type_id] = self.get_base(type)
            else:
                self.cipher[type_id] = self.get_from_spec(type, options)

        return self.cipher[type_id]

    def get_provider_class(self, type):
        return self.get_from_spec(type, class_only=True)

    def get_base(self, type, class_only=False):
        return self.get_provider(type, "base", {}, class_only=class_only)

    def get_from_spec(self, type, options=None, class_only=False):
        spec = self.get_type_spec(type)

        if not options:
            options = {}

        return self.get_provider(
            type,
            spec.get("provider", "base"),
            {**spec.get("options", {}), **options},
            class_only=class_only,
        )

    def get_provider(self, type, name, options, class_only=False):
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
            return provider_class(self.plugin_type, name, options)
        except Exception as error:
            raise EncryptionError(f"Encryption provider {name} error: {error}")


class Cipher(metaclass=MetaCipher):
    plugin_type = "encryption"
    cipher = {}
    states = {}
