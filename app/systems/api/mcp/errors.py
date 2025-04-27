class ServerError(Exception):
    def __init__(self, message, code=500):
        super().__init__(message)
        self.code = code

    def __str__(self):
        return f"{self.code}: {super().__str__()}"


class SessionNotFoundError(Exception):
    pass
