import sys
import traceback


def format_exception_info():
    exc_type, exc_value, exc_tb = sys.exc_info()
    return traceback.format_exception(exc_type, exc_value, exc_tb)


class ClientError(Exception):
    pass

class ConnectionError(ClientError):
    pass

class ParseError(ClientError):
    pass

class ResponseError(ClientError):

    def __init__(self, message, code = None, result = None):
        super().__init__(message)
        self.code = code
        self.result = result or message
