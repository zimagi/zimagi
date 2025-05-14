import binascii
import os

from systems.plugins.index import BasePlugin
from utility.filesystem import load_file


class BaseProvider(BasePlugin("encryption")):
    @classmethod
    def generate_key(self):
        size = 100
        return binascii.hexlify(os.urandom(size)).decode()[:size]

    def __init__(self, type, name, options=None):
        super().__init__(type, name)

        if not options:
            options = {}

        if options.get("key", None):
            if os.path.isfile(options["key"]):
                options["key"] = load_file(options["key"])

        self.initialize(options)
        self.import_config(options)

    def initialize(self, options):
        # Override in subclass if needed
        pass

    def encrypt(self, plain_text):
        # Plain Text - str|bytes -> str
        # Cipher Text - bytes
        self.validate()
        return self.encrypt_postprocess(self.encrypt_text(self.encrypt_preprocess(plain_text)))

    def encrypt_preprocess(self, plain_text):
        if isinstance(plain_text, bytes):
            plain_text = self.field_binary_marker + plain_text.hex()
        return str(plain_text)

    def encrypt_text(self, plain_text):
        # Override in providers
        return plain_text.encode()

    def encrypt_postprocess(self, cipher_text):
        # Override in providers if needed
        return cipher_text

    def decrypt(self, cipher_text, decode=True):
        # Cipher Text - bytes
        # Plain Text - str|bytes
        self.validate()
        return self.decrypt_postprocess(self.decrypt_text(self.decrypt_preprocess(cipher_text)), decode)

    def decrypt_preprocess(self, cipher_text):
        # Override in providers if needed
        return cipher_text

    def decrypt_text(self, cipher_text):
        # Override in providers
        return cipher_text

    def decrypt_postprocess(self, plain_text, decode):
        if decode and isinstance(plain_text, (bytes, bytearray)):
            plain_text = plain_text.decode(self.field_decoder)

        if isinstance(plain_text, str) and plain_text.startswith(self.field_binary_marker):
            plain_text = bytes.fromhex(plain_text[len(self.field_binary_marker) :])
        return plain_text
