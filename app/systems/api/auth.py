from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.utils.timezone import now

from coreapi import auth
from coreapi.utils import domain_matches
from rest_framework import permissions, authentication, exceptions

from systems.models.index import Model
from utility.encryption import Cipher
from utility.data import ensure_list

import logging


logger = logging.getLogger(__name__)


class CommandPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method == 'GET':
            return True
        elif not request.user:
            raise exceptions.AuthenticationFailed('Authentication credentials were not provided')

        auth_method = getattr(view, 'groups_allowed', None)
        if auth_method and callable(auth_method):
            groups = view.groups_allowed()

            if groups is False:
                return True

            return request.user.env_groups.filter(name__in = groups).exists()
        else:
            return True


class DataPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method not in ('GET', 'OPTIONS', 'HEAD'):
            raise exceptions.MethodNotAllowed(request.method)

        if not getattr(view, 'queryset', None):
            # Schema view should be accessible
            return True

        model_name = view.queryset.model._meta.data_name
        roles = settings.MANAGER.index.spec['data'].get(model_name, {}).get('roles', {})

        groups = roles.get('edit', [])
        if roles.get('view', None):
            groups.extend(ensure_list(roles['view']))

        if not groups:
            return False
        elif 'public' in groups:
            return True

        return request.user.env_groups.filter(name__in = groups).exists()


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



class APITokenAuthentication(authentication.TokenAuthentication):

    user_class = Model('user')


    def get_auth_header(self, request):
        return authentication.get_authorization_header(request)


    def validate_token_header(self, auth):
        if len(auth) == 1:
            msg = 'Invalid token header. No credentials provided.'
            logger.warning(msg)
            raise exceptions.AuthenticationFailed(msg)

        elif len(auth) > 2:
            msg = 'Invalid token header. Token string should not contain spaces.'
            logger.warning(msg)
            raise exceptions.AuthenticationFailed(msg)


    def authenticate_credentials(self, auth):
        self.validate_token_header(auth)

        components = auth[1].split('++')

        if len(components) != 2:
            raise exceptions.AuthenticationFailed('Invalid token. Required format: Token user++token')
        try:
            user = self.user_class.facade.retrieve(components[0])
            token = components[1]

        except self.user_class.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid token: User not found')

        if not user.is_active:
            raise exceptions.AuthenticationFailed('User account is inactive. Contact administrator')

        if not user.check_password(token):
            raise exceptions.AuthenticationFailed('Invalid token: User credentials are invalid')

        user.last_login = now()
        user.save()

        self.user_class.facade.set_active_user(user)
        return (user, token)


class CommandAPITokenAuthentication(APITokenAuthentication):

    def authenticate(self, request):
        if request.method == 'POST':
            # All command execution comes through POST requests
            try:
                auth = Cipher.get('token').decrypt(self.get_auth_header(request)).split()
            except Exception as e:
                msg = 'Invalid token header. Credentials can not be decrypted.'
                logger.warning(msg)
                raise exceptions.AuthenticationFailed(msg)

            if not auth or auth[0].lower() != self.keyword.lower():
                raise exceptions.AuthenticationFailed("Authentication header required: 'Authorization = {} user++token'".format(self.keyword))

            return self.authenticate_credentials(auth)
        else:
            # Schema view (list all commands in the system)
            return None


class DataAPITokenAuthentication(APITokenAuthentication):

    def authenticate(self, request):
        auth = self.get_auth_header(request).split()

        if not auth or auth[0].lower() != self.keyword.lower():
            # Support public access of resources
            return None

        return self.authenticate_credentials(auth)
