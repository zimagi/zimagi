import base64
import logging
import sys
from urllib import request as downloader

import magic
import oyaml

from .. import utility

logger = logging.getLogger(__name__)


class Message:
    @classmethod
    def get(cls, data, cipher=None):
        message = cipher.decrypt(data["package"], False) if cipher else data
        data = utility.load_json(message) if isinstance(message, (str, bytes)) else data["package"]

        msg = getattr(sys.modules[__name__], data["type"])()
        msg.load(data)
        return msg

    def __init__(self, message="", name=None, prefix="", silent=False, system=False):
        super().__init__()

        self.type = self.__class__.__name__
        self.name = name
        self.prefix = prefix
        self.message = message
        self.silent = silent
        self.system = system

    def load(self, data):
        for field, value in data.items():
            if field != "type":
                setattr(self, field, value)

    def is_error(self):
        return False

    def render(self):
        data = {"type": self.type, "message": self.message}
        if self.name:
            data["name"] = self.name

        if self.prefix:
            data["prefix"] = self.prefix

        if self.silent:
            data["silent"] = self.silent

        if self.system:
            data["system"] = self.system

        return data

    def to_json(self):
        return utility.dump_json(self.render())

    def format(self, debug=False, width=None):
        return f"{self.prefix}{self.message}"

    def display(self, debug=False, width=None):
        if not self.silent:
            sys.stdout.write(f"{self.format(debug=debug, width=width)}\n")
            sys.stdout.flush()


class StatusMessage(Message):
    def __init__(self, success=True):
        super().__init__(success)

    def format(self, debug=False, disable_color=False, width=None):
        return f"Success: {self.message}"

    def display(self, debug=False, disable_color=False, width=None):
        pass


class DataMessage(Message):

    def __init__(self, message="", data=None, name=None, prefix="", silent=False, system=False):
        super().__init__(message, name=name, prefix=prefix, silent=silent, system=system)
        self.data = data

    def load(self, data):
        super().load(data)
        self.data = utility.normalize_value(self.data, strip_quotes=True, parse_json=True)

    def render(self):
        result = super().render()
        result["data"] = self.data
        return result

    def format(self, debug=False, width=None):
        data = self.data
        if isinstance(self.data, (list, tuple, dict)):
            data_render = oyaml.dump(self.data, indent=2)
            data = f"\n{data_render}"

        return f"{self.message}: {data}"


class InfoMessage(Message):
    pass


class NoticeMessage(Message):
    pass


class SuccessMessage(Message):
    pass


class WarningMessage(Message):
    def display(self, debug=False, width=None):
        if not self.silent:
            formatted_warning = self.format(debug=debug)
            sys.stderr.write(f"{formatted_warning}\n")
            sys.stderr.flush()


class ErrorMessage(Message):

    def __init__(self, message="", traceback=None, name=None, prefix="", silent=False, system=False):
        super().__init__(message, name=name, prefix=prefix, silent=silent, system=system)
        self.traceback = traceback

    def is_error(self):
        return True

    def render(self):
        result = super().render()
        result["traceback"] = self.traceback
        return result

    def format(self, debug=False, width=None):
        if debug:
            traceback = [item.strip() for item in self.traceback]
            traceback_message = "\n".join(traceback)
            return f"\n{self.prefix}** {self.message}\n\n> {traceback_message}\n"
        return f"{self.prefix}** {self.message}"

    def display(self, debug=False, width=None):
        if not self.silent and self.message:
            sys.stderr.write(f"{self.format(debug=debug, width=width)}\n")
            sys.stderr.flush()


class TableMessage(Message):

    def __init__(self, message="", name=None, prefix="", silent=False, system=False, row_labels=False):
        super().__init__(message, name=name, prefix=prefix, silent=silent, system=system)
        self.row_labels = row_labels

    def load(self, data):
        super().load(data)
        self.message = utility.normalize_value(self.message, strip_quotes=True, parse_json=True)

    def render(self):
        result = super().render()
        result["row_labels"] = self.row_labels
        return result

    def format(self, debug=False, width=None):
        return utility.format_data(self.message, self.prefix, row_labels=self.row_labels, width=width)


class ImageMessage(Message):

    def __init__(self, location, name=None, silent=True, system=False):
        super().__init__(location, name=name, silent=silent, system=system)

    def load(self, data):
        super().load(data)

        if utility.validate_url(self.message):
            with downloader.urlopen(self.message) as image:
                image_bytes = image.read()
        else:
            with open(self.message, mode="rb") as image:
                image_bytes = image.read()

        self.data = base64.b64encode(image_bytes)
        try:
            self.mimetype = magic.from_buffer(image_bytes, mime=True)
        except Exception:
            self.mimetype = None

    def render(self):
        result = super().render()
        result["data"] = self.data
        result["mimetype"] = self.mimetype
        return result
