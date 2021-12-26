from coreapi import auth
from coreapi.utils import domain_matches
from rest_framework import permissions, exceptions

from systems.api.auth import APITokenAuthentication
from utility.encryption import Cipher

import re
import logging


logger = logging.getLogger(__name__)


class CommandPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        return view.check_execute(request.user)


class CommandClientTokenAuthentication(auth.TokenAuthentication):

    def __init__(self, user, token, scheme = None, domain = None):
        super().__init__(token, scheme, domain)
        self.user = user

    def __call__(self, request):
        if not domain_matches(request, self.domain):
            return request

        token = "{} {}++{}".format(self.scheme, self.user, self.token)
        request.headers['Authorization'] = Cipher.get('token').encrypt(token)
        return request


class CommandAPITokenAuthentication(APITokenAuthentication):

    def authenticate(self, request):
        try:
            token_text = self.get_auth_header(request)
            if not token_text and re.search(r'^(/|/status/?)$', request.path):
                return None

            auth = Cipher.get('token').decrypt(token_text).split()

        except Exception as e:
            msg = 'Invalid token header. Credentials can not be decrypted'
            logger.warning("{}: {}".format(msg, token_text))
            raise exceptions.AuthenticationFailed(msg)

        if not auth or auth[0].lower() != self.keyword.lower():
            raise exceptions.AuthenticationFailed("Authentication header required: 'Authorization = {} <user_name>++<token>'".format(self.keyword))

        return self.authenticate_credentials(auth)
