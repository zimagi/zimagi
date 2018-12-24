from os import path
from datetime import datetime

from Crypto.Cipher import AES
from Crypto.Util import Counter
from Crypto import Random

import base64
import hashlib
import string
import random
import binascii


class AESCipher:

    @classmethod
    def generate_key(cls):
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.SystemRandom().choice(chars) for _ in range(32))


    def __init__(self, key = None):
        self.batch_size = AES.block_size
        
        if key:
            if path.isfile(key):
                with open(key,'r') as file:
                    key = file.read()
            
            self.key = hashlib.sha256(key.encode()).digest()
        else:
            self.key = self.__class__.generate_key()


    def encrypt(self, message):
        iv = Random.new().read(self.batch_size)
        iv_int = int(binascii.hexlify(iv), self.batch_size)
        ctr = Counter.new(self.batch_size * 8, initial_value = iv_int)
        
        cipher = AES.new(self.key, AES.MODE_CTR, counter = ctr)
        return base64.b64encode(iv + cipher.encrypt(message)) 

    def decrypt(self, ciphertext):
        ciphertext = base64.b64decode(ciphertext)
        iv = ciphertext[:self.batch_size]
        ciphertext = ciphertext[self.batch_size:]
       
        iv_int = int(iv.hex(), self.batch_size)
        ctr = Counter.new(self.batch_size * 8, initial_value = iv_int)
       
        cipher = AES.new(self.key, AES.MODE_CTR, counter = ctr)
        return cipher.decrypt(ciphertext).decode("utf-8") 
