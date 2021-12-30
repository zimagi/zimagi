from . import encryption


class ClientTokenAuthentication(object):

    def __init__(self,
        user,
        token,
        encryption_key = None
    ):
        self.scheme = 'Token'
        self.user = user
        self.token = token
        self.cipher = encryption.Cipher.get(encryption_key)


    def __call__(self, request):
        request.headers['Authorization'] = "{} {} {}".format(
            self.scheme,
            self.user,
            self.cipher.encrypt(self.token).decode('utf-8')
        )
        return request
