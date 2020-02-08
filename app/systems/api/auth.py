from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.utils.timezone import now

from coreapi import auth
from coreapi.utils import domain_matches
from rest_framework import permissions, authentication, exceptions

from data.user.models import User
from utility.encryption import Cipher

import logging


logger = logging.getLogger(__name__)


class CommandPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        auth_method = getattr(view, 'groups_allowed', None)

        if auth_method and callable(auth_method):
            groups = view.groups_allowed()

            if groups is False:
                return True

            return request.user.env_groups.filter(name__in=groups).exists()
        else:
            return True


class EncryptedAPITokenAuthentication(authentication.TokenAuthentication):

    def authenticate(self, request):
        header = authentication.get_authorization_header(request)

        if request.method == 'POST':
            try:
                auth = Cipher.get('token').decrypt(header).split()
            except Exception as e:
                msg = 'Invalid token header. Credentials can not be decrypted.'
                logger.warning(msg)
                raise exceptions.AuthenticationFailed(msg)

            if not auth or auth[0].lower() != self.keyword.lower():
                return None

            if len(auth) == 1:
                msg = 'Invalid token header. No credentials provided.'
                logger.warning(msg)
                raise exceptions.AuthenticationFailed(msg)
            elif len(auth) > 2:
                msg = 'Invalid token header. Token string should not contain spaces.'
                logger.warning(msg)
                raise exceptions.AuthenticationFailed(msg)

            (user, token) = self.authenticate_credentials(auth[1])
        else:
            user = User.facade.retrieve(settings.ADMIN_USER)
            token = None

        User.facade.set_active_user(user)
        return (user, token)

    def authenticate_credentials(self, key):
        components = key.split('++')

        if len(components) != 2:
            raise exceptions.AuthenticationFailed('Invalid token. Required format: Token user++token')
        try:
            user = User.objects.get(name = components[0])
            token = components[1]
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid token: User not found')

        if not user.is_active:
            raise exceptions.AuthenticationFailed('User account is inactive. Contact administrator')

        if not user.check_password(token):
            raise exceptions.AuthenticationFailed('Invalid token: User credentials are invalid')

        user.last_login = now()
        user.save()

        return (user, token)


class EncryptedClientTokenAuthentication(auth.TokenAuthentication):

    def __init__(self, user, token, scheme = None, domain = None):
        super().__init__(token, scheme, domain)
        self.user = user

    def __call__(self, request):
        if not domain_matches(request, self.domain):
            return request

        token = "{} {}++{}".format(self.scheme, self.user, self.token)
        request.headers['Authorization'] = Cipher.get('token').encrypt(token)
        return request
