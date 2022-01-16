from systems.encryption.cipher import Cipher
from utility.runtime import Runtime
from utility.terminal import TerminalMixin
from utility.data import normalize_value, dump_json, load_json
from utility.display import format_data

import sys
import logging


logger = logging.getLogger(__name__)


class AppMessage(TerminalMixin):

    @classmethod
    def get(cls, data, decrypt = True, user = None):
        if decrypt:
            message = Cipher.get('command_api', user = user).decrypt(data['package'], False)
            data = load_json(message)

        message = getattr(sys.modules[__name__], data['type'])(user = user)
        message.load(data)
        return message


    def __init__(self, message = '', name = None, prefix = None, silent = False, user = None):
        super().__init__()

        self.type = self.__class__.__name__
        self.name = name
        self.prefix = prefix
        self.message = message
        self.silent = silent
        self.cipher = Cipher.get('command_api', user = user)


    def is_error(self):
        return False


    def load(self, data):
        for field, value in data.items():
            if field != 'type':
                setattr(self, field, value)

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
        return dump_json(self.render())

    def to_package(self):
        json_text = self.to_json()
        cipher_text = self.cipher.encrypt(json_text).decode(self.cipher.field_decoder)
        package = dump_json({ 'package': cipher_text }) + "\n"
        return package


    def format(self, debug = False, disable_color = False, width = None):
        return "{}{}".format(self._format_prefix(disable_color), self.message)

    def _format_prefix(self, disable_color):
        if self.prefix:
            prefix = self.prefix if disable_color else self.prefix_color(self.prefix)
            return prefix + ' '
        else:
            return ''

    def display(self, debug = False, disable_color = False, width = None):
        if not self.silent:
            self.print(self.format(
                debug = debug,
                disable_color = disable_color,
                width = width
            ), sys.stdout)
            sys.stdout.flush()


class DataMessage(AppMessage):

    def __init__(self, message = '', data = None, name = None, prefix = None, silent = False, user = None):
        super().__init__(message,
            name = name,
            prefix = prefix,
            silent = silent,
            user = user
        )
        self.data = data

    def load(self, data):
        super().load(data)
        self.data = normalize_value(self.data, strip_quotes = True, parse_json = True)


    def render(self):
        result = super().render()
        result['data'] = self.data
        return result

    def format(self, debug = False, disable_color = False, width = None):
        data = self.data if disable_color else self.value_color(self.data)
        return "{}{}: {}".format(
            self._format_prefix(disable_color),
            self.message,
            data
        )


class InfoMessage(AppMessage):
    pass


class NoticeMessage(AppMessage):

    def format(self, debug = False, disable_color = False, width = None):
        message = self.message if disable_color else self.notice_color(self.message)
        return "{}{}".format(self._format_prefix(disable_color), message)


class SuccessMessage(AppMessage):

    def format(self, debug = False, disable_color = False, width = None):
        message = self.message if disable_color else self.success_color(self.message)
        return "{}{}".format(self._format_prefix(disable_color), message)


class WarningMessage(AppMessage):

    def format(self, debug = False, disable_color = False, width = None):
        message = self.message if disable_color else self.warning_color(self.message)
        return "{}{}".format(self._format_prefix(disable_color), message)

    def display(self, debug = False, disable_color = False, width = None):
        if not self.silent:
            self.print(self.format(debug), sys.stderr)
            sys.stderr.flush()


class ErrorMessage(AppMessage):

    def __init__(self, message = '', traceback = None, name = None, prefix = None, silent = False, user = None):
        super().__init__(message,
            name = name,
            prefix = prefix,
            silent = silent,
            user = user
        )
        self.traceback = traceback

    def is_error(self):
        return True

    def render(self):
        result = super().render()
        result['traceback'] = self.traceback
        return result

    def format(self, debug = False, disable_color = False, width = None):
        message = self.message if disable_color else self.error_color(self.message)
        if Runtime.debug() or debug:
            traceback = [ item.strip() for item in self.traceback ]
            traceback_message = "\n".join(traceback) if disable_color else self.traceback_color("\n".join(traceback))
            return "\n{}** {}\n\n> {}\n".format(
                self._format_prefix(disable_color),
                message,
                traceback_message
            )
        return "{}** {}".format(self._format_prefix(disable_color), message)

    def display(self, debug = False, disable_color = False, width = None):
        if not self.silent and self.message:
            self.print(self.format(
                debug = debug,
                disable_color = disable_color,
                width = width
            ), sys.stderr)
            sys.stderr.flush()


class TableMessage(AppMessage):

    def __init__(self, message = '', name = None, prefix = None, silent = False, row_labels = False, user = None):
        super().__init__(message,
            name = name,
            prefix = prefix,
            silent = silent,
            user = user
        )
        self.row_labels = row_labels

    def load(self, data):
        super().load(data)
        self.message = normalize_value(self.message, strip_quotes = True, parse_json = False)


    def render(self):
        result = super().render()
        result['row_labels'] = self.row_labels
        return result

    def format(self, debug = False, disable_color = False, width = None):
        return format_data(self.message, self._format_prefix(disable_color),
            row_labels = self.row_labels,
            width = width
        )
