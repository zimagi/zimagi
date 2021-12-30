import sys
import traceback


def format_exception_info():
    exc_type, exc_value, exc_tb = sys.exc_info()
    return traceback.format_exception(exc_type, exc_value, exc_tb)


class ParameterError(Exception):
    pass

class CodecError(Exception):
    pass

class CommandError(Exception):
    pass

class CommandClientError(CommandError):
    pass

class CommandParseError(CommandError):
    pass

class CommandConnectionError(CommandError):
    pass

class CommandResponseError(CommandError):
    pass

class DataError(Exception):
    pass

class DataParseError(DataError):
    pass
