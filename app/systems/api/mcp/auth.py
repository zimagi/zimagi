from starlette.authentication import AuthCredentials, AuthenticationBackend, AuthenticationError, SimpleUser

from systems.api.auth import APITokenAuthenticationMixin


class ZimagiUser(SimpleUser):
    def __init__(self, user):
        super().__init__(user.email)
        self.zimagi = user


class TokenAuthBackend(APITokenAuthenticationMixin, AuthenticationBackend):
    api_type = "mcp_api"
    keyword = "Bearer"

    def raise_auth_failed(self, message):
        raise AuthenticationError(message)

    async def authenticate(self, connection):
        if "Authorization" not in connection.headers:
            return

        user, token = self.parse_token(connection.headers["Authorization"])
        self.check_login(user, token)

        return AuthCredentials(["authenticated"]), ZimagiUser(user)

    def check_token(self, user, token):
        if not (user.check_password(token) or (user.temp_token and token == user.temp_token)):
            self.raise_auth_failed("Invalid token: User credentials are invalid")
