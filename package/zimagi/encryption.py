from Crypto.Cipher import AES
from Crypto.Util import Counter
from Crypto import Random

import base64
import binascii


class Cipher(object):

    @classmethod
    def get(cls, key = None):
        return AESCipher(key) if key else NullCipher()


class NullCipher(object):

    def __init__(self, key = None):
        self.key = key


    def encrypt(self, message):
        return str(message).encode()

    def decrypt(self, ciphertext, decode = True):
        if decode and isinstance(ciphertext, (bytes, bytearray)):
            ciphertext = ciphertext.decode("utf-8")
        return ciphertext


class AESCipher(object):

    def __init__(self, key):
        self.binary_marker = '<<<<-->BINARY<-->>>>'
        self.batch_size = AES.block_size
        self.key = key


    def encrypt(self, message):
        iv = Random.new().read(self.batch_size)
        iv_int = int(binascii.hexlify(iv), self.batch_size)
        ctr = Counter.new(self.batch_size * 8, initial_value = iv_int)

        cipher = AES.new(self.key.encode(), AES.MODE_CTR, counter = ctr)

        if isinstance(message, bytes):
            message = self.binary_marker + message.hex()
        return base64.b64encode(iv + cipher.encrypt(str(message).encode()))

    def decrypt(self, ciphertext, decode = True):
        ciphertext = base64.b64decode(ciphertext)
        iv = ciphertext[:self.batch_size]
        ciphertext = ciphertext[self.batch_size:]

        iv_int = int(iv.hex(), self.batch_size)
        ctr = Counter.new(self.batch_size * 8, initial_value = iv_int)

        cipher = AES.new(self.key.encode(), AES.MODE_CTR, counter = ctr)
        message = cipher.decrypt(ciphertext)

        if decode:
            message = message.decode("utf-8")
        if isinstance(message, str) and message.startswith(self.binary_marker):
            message = bytes.fromhex(message[len(self.binary_marker):])

        return message
