from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from coreapi import auth
from coreapi.utils import domain_matches
from rest_framework import permissions, authentication, exceptions

from utility.encryption import Cipher


class CommandPermission(permissions.BasePermission):
    
    def has_permission(self, request, view):
        auth_method = getattr(view, 'groups_allowed', None)

        if auth_method and callable(auth_method):
            groups = view.groups_allowed()

            if not groups:
                return True

            return request.user.groups.filter(name__in=groups).exists()
        else:
            return True


class EncryptedAPITokenAuthentication(authentication.TokenAuthentication):
    
    def authenticate(self, request):
        header = authentication.get_authorization_header(request)
        auth = Cipher.get().decrypt(header).split()

        if not auth or auth[0].lower() != self.keyword.lower():
            return None

        if len(auth) == 1:
            msg = _('Invalid token header. No credentials provided.')
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = _('Invalid token header. Token string should not contain spaces.')
            raise exceptions.AuthenticationFailed(msg)

        return self.authenticate_credentials(auth[1])


class EncryptedClientTokenAuthentication(auth.TokenAuthentication):
    
    def __call__(self, request):
        if not domain_matches(request, self.domain):
            return request
        
        token = "{} {}".format(self.scheme, self.token)
        request.headers['Authorization'] = Cipher.get().encrypt(token)
        return request
