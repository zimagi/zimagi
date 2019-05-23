from django.utils.module_loading import import_string

from utility.runtime import Runtime
from utility.terminal import TerminalMixin
from utility.encryption import Cipher
from utility.display import format_data

import sys
import json
import logging


logger = logging.getLogger(__name__)


class AppMessage(TerminalMixin):

    cipher = Cipher.get('message')

    @classmethod
    def get(cls, data, decrypt = True):
        if decrypt:
            message = cls.cipher.decrypt(data['package'], False)
            data = json.loads(message)

        try:
            msg = import_string(data['type'])
        except Exception:
            msg = getattr(sys.modules[__name__], data['type'])()

        msg.load(data)
        return msg


    def __init__(self, message = '', name = None, prefix = None, silent = False):
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
        return json.dumps(self.render())

    def to_package(self):
        json_text = self.to_json()
        cipher_text = self.__class__.cipher.encrypt(json_text).decode('utf-8')
        package = json.dumps({ 'package': cipher_text }) + "\n"
        return package


    def format(self, debug = False):
        return "{}{}".format(self._format_prefix(), self.message)

    def _format_prefix(self):
        if self.prefix:
            return self.prefix_color(self.prefix) + ' '
        else:
            return ''

    def display(self, debug = False):
        if not self.silent:
            self.print(self.format(debug), sys.stdout)
            sys.stdout.flush()


class DataMessage(AppMessage):

    def __init__(self, message = '', data = None, name = None, prefix = None, silent = False):
        super().__init__(message,
            name = name,
            prefix = prefix,
            silent = silent
        )
        self.data = data

    def render(self):
        result = super().render()
        result['data'] = self.data
        return result

    def format(self, debug = False):
        return "{}{}: {}".format(
            self._format_prefix(),
            self.message,
            self.value_color(self.data)
        )


class InfoMessage(AppMessage):
    pass


class NoticeMessage(AppMessage):

    def format(self, debug = False):
        return "{}{}".format(self._format_prefix(), self.notice_color(self.message))


class SuccessMessage(AppMessage):

    def format(self, debug = False):
        return "{}{}".format(self._format_prefix(), self.success_color(self.message))


class WarningMessage(AppMessage):

    def format(self, debug = False):
        return "{}{}".format(self._format_prefix(), self.warning_color(self.message))

    def display(self, debug = False):
        if not self.silent:
            self.print(self.format(debug), sys.stderr)
            sys.stderr.flush()


class ErrorMessage(AppMessage):

    def __init__(self, message = '', traceback = None, name = None, prefix = None, silent = False):
        super().__init__(message,
            name = name,
            prefix = prefix,
            silent = silent
        )
        self.traceback = traceback

    def render(self):
        result = super().render()
        result['traceback'] = self.traceback
        return result

    def format(self, debug = False):
        if Runtime.debug() or debug:
            traceback = [ item.strip() for item in self.traceback ]
            return "\n{}** {}\n\n> {}\n".format(
                self._format_prefix(),
                self.error_color(self.message),
                self.traceback_color("\n".join(traceback))
            )
        return "{}** {}".format(self._format_prefix(), self.error_color(self.message))

    def display(self, debug = False):
        if not self.silent and self.message:
            self.print(self.format(debug), sys.stderr)
            sys.stderr.flush()


class TableMessage(AppMessage):

    def __init__(self, message = '', name = None, prefix = None, silent = False, row_labels = False):
        super().__init__(message,
            name = name,
            prefix = prefix,
            silent = silent
        )
        self.row_labels = row_labels

    def format(self, debug = False):
        return format_data(self.message, self._format_prefix(), row_labels = self.row_labels)
