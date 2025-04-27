import logging
import re

from django.utils.timezone import now
from rest_framework import authentication, exceptions

from systems.models.index import Model

logger = logging.getLogger(__name__)


class APITokenAuthenticationMixin(object):
    api_type = None
    keyword = "Token"

    @classmethod
    def get_user_class(cls):
        if not getattr(cls, "_user_class", None):
            cls._user_class = Model("user")
        return cls._user_class

    def raise_auth_failed(self, message):
        raise NotImplementedError("Classes including APITokenAuthenticationMixin should implement raise_auth_failed method.")

    def parse_token(self, token_text):
        user_class = self.get_user_class()
        auth_components = re.split(r"\s+", token_text)

        if len(auth_components) != 3:
            self.raise_auth_failed(f"Invalid token. Required format: {self.keyword} <user_name> <token>")
        if auth_components[0].lower() != self.keyword.lower():
            self.raise_auth_failed(f"Authentication header required: 'Authorization: {self.keyword} <user_name> <token>'")

        try:
            user = user_class.facade.retrieve(auth_components[1])
            token = auth_components[2].strip()

        except user_class.DoesNotExist:
            self.raise_auth_failed("Invalid token: User not found")

        return (user, token)

    def check_login(self, user, token):
        from systems.encryption.cipher import Cipher

        user_class = self.get_user_class()
        try:
            if self.api_type:
                token = Cipher.get(self.api_type, user=user.name).decrypt(token)

        except Exception as error:
            self.raise_auth_failed("Invalid token header. Credentials can not be decrypted")

        if not user.is_active:
            self.raise_auth_failed("User account is inactive. Contact administrator")

        self.check_token(user, token)

        user.last_login = now()
        user.save()

        user_class.facade.set_active_user(user)

    def check_token(self, user, token):
        if not user.check_password(token):
            self.raise_auth_failed("Invalid token: User credentials are invalid")


class APITokenAuthentication(APITokenAuthenticationMixin, authentication.TokenAuthentication):

    def raise_auth_failed(self, message):
        raise exceptions.AuthenticationFailed(message)

    def get_auth_header(self, request):
        header = authentication.get_authorization_header(request)
        if header and isinstance(header, (bytes, bytearray)):
            header = header.decode("utf-8")
        return header

    def authenticate(self, request):
        token_text = self.get_auth_header(request)
        if not token_text:
            return None

        user, token = self.parse_token(token_text)
        self.check_login(user, token)

        return (user, token)
