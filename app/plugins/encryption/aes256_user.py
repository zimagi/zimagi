from systems.encryption.cipher import EncryptionError
from systems.plugins.index import BaseProvider


class Provider(BaseProvider("encryption", "aes256_user")):
    def initialize(self, options):
        if options.get("user", None):
            user_facade = self.manager.index.get_facade_index()["user"]
            user = user_facade.retrieve(options["user"])
            if not user:
                raise EncryptionError("User {} does not exist".format(options["user"]))

            options["key"] = user.encryption_key
