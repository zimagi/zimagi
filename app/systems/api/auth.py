from django.utils.timezone import now
from rest_framework import authentication, exceptions

from systems.models.index import Model

import logging


logger = logging.getLogger(__name__)


class APITokenAuthentication(authentication.TokenAuthentication):

    user_class = Model('user')


    def get_auth_header(self, request):
        header = authentication.get_authorization_header(request)
        if header and isinstance(header, (bytes, bytearray)):
            header = header.decode('utf-8')
        return header


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
