from .. import utility

import sys
import logging


logger = logging.getLogger(__name__)


class Message(object):

    @classmethod
    def get(cls, data, cipher = None):
        message = cipher.decrypt(data['package'], False) if cipher else data
        data = utility.load_json(message) if isinstance(message, (str, bytes)) else data['package']

        msg = getattr(sys.modules[__name__], data['type'])()
        msg.load(data)
        return msg


    def __init__(self, message = '', name = None, prefix = '', silent = False):
        super().__init__()

        self.type = self.__class__.__name__
        self.name = name
        self.prefix = prefix
        self.message = message
        self.silent = silent


    def load(self, data):
        for field, value in data.items():
            if field != 'type':
                setattr(self, field, value)


    def is_error(self):
        return False


    def render(self):
        data = {
            'type': self.type,
            'message': self.message
        }
        if self.name:
            data['name'] = self.name

        if self.prefix:
            data['prefix'] = self.prefix

        if self.silent:
            data['silent'] = self.silent

        return data

    def to_json(self):
        return utility.dump_json(self.render())

    def format(self, debug = False, width = None):
        return "{}{}".format(self.prefix, self.message)

    def display(self, debug = False, width = None):
        if not self.silent:
            sys.stdout.write("{}\n".format(self.format(
                debug = debug,
                width = width
            )))
            sys.stdout.flush()


class StatusMessage(Message):

    def __init__(self, success = True):
        super().__init__(success)

    def format(self, debug = False, disable_color = False, width = None):
        return "Success: {}".format(self.message)

    def display(self, debug = False, disable_color = False, width = None):
        pass


class DataMessage(Message):

    def __init__(self, message = '', data = None, name = None, prefix = '', silent = False):
        super().__init__(message,
            name = name,
            prefix = prefix,
            silent = silent
        )
        self.data = data

    def load(self, data):
        super().load(data)
        self.data = utility.normalize_value(self.data, strip_quotes = True, parse_json = True)


    def render(self):
        result = super().render()
        result['data'] = self.data
        return result

    def format(self, debug = False, width = None):
        return "{}{}: {}".format(self.prefix, self.message, self.data)


class InfoMessage(Message):
    pass


class NoticeMessage(Message):
    pass


class SuccessMessage(Message):
    pass


class WarningMessage(Message):

    def display(self, debug = False, width = None):
        if not self.silent:
            sys.stderr.write("{}\n".format(self.format(debug = debug)))
            sys.stderr.flush()


class ErrorMessage(Message):

    def __init__(self, message = '', traceback = None, name = None, prefix = '', silent = False):
        super().__init__(message,
            name = name,
            prefix = prefix,
            silent = silent
        )
        self.traceback = traceback

    def is_error(self):
        return True

    def render(self):
        result = super().render()
        result['traceback'] = self.traceback
        return result

    def format(self, debug = False, width = None):
        if debug:
            traceback = [ item.strip() for item in self.traceback ]
            traceback_message = "\n".join(traceback)
            return "\n{}** {}\n\n> {}\n".format(
                self.prefix,
                self.message,
                traceback_message
            )
        return "{}** {}".format(self.prefix, self.message)

    def display(self, debug = False, width = None):
        if not self.silent and self.message:
            sys.stderr.write("{}\n".format(self.format(
                debug = debug,
                width = width
            )))
            sys.stderr.flush()


class TableMessage(Message):

    def __init__(self, message = '', name = None, prefix = '', silent = False, row_labels = False):
        super().__init__(message,
            name = name,
            prefix = prefix,
            silent = silent
        )
        self.row_labels = row_labels

    def load(self, data):
        super().load(data)
        self.message = utility.normalize_value(self.message, strip_quotes = True, parse_json = True)


    def render(self):
        result = super().render()
        result['row_labels'] = self.row_labels
        return result

    def format(self, debug = False, width = None):
        return utility.format_data(self.message, self.prefix,
            row_labels = self.row_labels,
            width = width
        )
