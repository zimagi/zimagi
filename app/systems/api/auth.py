import logging
import re

from django.utils.timezone import now
from rest_framework import authentication, exceptions
from systems.encryption.cipher import Cipher
from systems.models.index import Model

logger = logging.getLogger(__name__)


class APITokenAuthentication(authentication.TokenAuthentication):
    user_class = Model("user")
    api_type = None

    def get_auth_header(self, request):
        header = authentication.get_authorization_header(request)
        if header and isinstance(header, (bytes, bytearray)):
            header = header.decode("utf-8")
        return header

    def parse_token(self, token_text):
        auth_components = re.split(r"\s+", token_text)

        if len(auth_components) != 3:
            raise exceptions.AuthenticationFailed(f"Invalid token. Required format: {self.keyword} <user_name> <token>")
        if auth_components[0].lower() != self.keyword.lower():
            raise exceptions.AuthenticationFailed(
                f"Authentication header required: 'Authorization: {self.keyword} <user_name> <token>'"
            )

        try:
            user = self.user_class.facade.retrieve(auth_components[1])
            token = auth_components[2].strip()

        except self.user_class.DoesNotExist:
            raise exceptions.AuthenticationFailed("Invalid token: User not found")

        return (user, token)

    def authenticate(self, request):
        token_text = self.get_auth_header(request)
        if not token_text:
            return None

        user, token = self.parse_token(token_text)
        try:
            if self.api_type:
                token = Cipher.get(self.api_type, user=user.name).decrypt(token)

        except Exception as error:
            raise exceptions.AuthenticationFailed("Invalid token header. Credentials can not be decrypted")

        if not user.is_active:
            raise exceptions.AuthenticationFailed("User account is inactive. Contact administrator")
        if not user.check_password(token):
            raise exceptions.AuthenticationFailed("Invalid token: User credentials are invalid")

        user.last_login = now()
        user.save()

        self.user_class.facade.set_active_user(user)
        return (user, token)
