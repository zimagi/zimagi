from django.conf import settings
from rest_framework.response import Response
from systems.encryption.cipher import Cipher


class EncryptedResponse(Response):
    api_type = None

    def __init__(self, user=None, api_type=None, **kwargs):
        super().__init__(**kwargs)
        self.user = user

        if api_type:
            self.api_type = api_type

    @property
    def rendered_content(self):
        if not self.api_type or not getattr(
            settings, "ENCRYPT_{}_API".format(self.api_type.replace("_api", "").upper()), True
        ):
            return super().rendered_content
        return Cipher.get(self.api_type, user=self.user).encrypt(super().rendered_content)
