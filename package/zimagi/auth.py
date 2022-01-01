from requests import auth


class ClientTokenAuthentication(auth.AuthBase):

    def __init__(self,
        user,
        token,
        cipher = None
    ):
        self.user = user
        self.token = token
        self.cipher = cipher
        self.encrypted = False


    def __call__(self, request):
        if not self.encrypted and self.cipher:
            self.token = self.cipher.encrypt(self.token).decode('utf-8')
            self.encrypted = True

        request.headers['Authorization'] = "Token {} {}".format(
            self.user,
            self.token
        )
        return request
