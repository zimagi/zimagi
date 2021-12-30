from Crypto.Cipher import AES
from Crypto.Util import Counter
from Crypto import Random

from systems.plugins.index import BaseProvider

import base64
import hashlib
import binascii


class Provider(BaseProvider('encryption', 'aes256')):

    @classmethod
    def generate_key(self):
        return hashlib.sha256(super().generate_key().encode()).hexdigest()[::2]


    def initialize(self, options):
        options['key'] = hashlib.sha256(options['key'].encode()).hexdigest()[::2]


    def encrypt_text(self, plain_text):
        iv = Random.new().read(AES.block_size)
        iv_int = int(binascii.hexlify(iv), AES.block_size)
        ctr = Counter.new(AES.block_size * 8, initial_value = iv_int)

        cipher = AES.new(self.field_key.encode(), AES.MODE_CTR, counter = ctr)
        return base64.b64encode(iv + cipher.encrypt(plain_text.encode()))


    def decrypt_text(self, cipher_text):
        cipher_text = base64.b64decode(cipher_text)
        iv = cipher_text[:AES.block_size]
        cipher_text = cipher_text[AES.block_size:]

        iv_int = int(iv.hex(), AES.block_size)
        ctr = Counter.new(AES.block_size * 8, initial_value = iv_int)

        cipher = AES.new(self.field_key.encode(), AES.MODE_CTR, counter = ctr)
        return cipher.decrypt(cipher_text)
