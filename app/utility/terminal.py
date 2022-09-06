from zoneinfo import ZoneInfo
from django.conf import settings

from .runtime import Runtime

import sys
import re
import colorful


def colorize_data(data):
    if isinstance(data, dict):
        for key, value in data.items():
            data[key] = colorize_data(value)
    elif isinstance(data, (list, tuple)):
        data = list(data)
        for index, value in enumerate(data):
            data[index] = colorize_data(value)
    elif isinstance(data, str):
        try:
            return colorful.format(data)
        except Exception as e:
            pass
    return data


class TerminalMixin(object):

    def exit(self, code = 0):
        sys.exit(code)


    def format_time(self, date_time, format = "%Y-%m-%d %I:%M:%S %p"):
        return date_time.astimezone(ZoneInfo(settings.TIME_ZONE)).strftime(format)


    def print(self, message = '', stream = sys.stdout):
        with settings.DISPLAY_LOCK:
            plain_text = self.raw_text(message)

            if Runtime.color() and plain_text != message:
                try:
                    colorful.print(message, file = stream)
                except Exception:
                    stream.write(plain_text + "\n")
            else:
                stream.write(plain_text + "\n")

    def raw_text(self, message):
        message = re.sub(r'\{c\.[^\}]+\}', '', message)
        return message


    def style(self, style, message = None, func = True):
        def _format(output):
            if Runtime.color():
                output = re.sub(r'([\{\}])', r'\1\1', str(output))
                lines = []
                for line in output.split("\n"):
                    lines.append('{c.' + style + '}' + line + '{c.reset}')
                return "\n".join(lines)
            else:
                return output

        if not func or message is not None:
            return _format(str(message))
        else:
            return _format


    def yellow(self, message = None, func = True):
        return self.style('yellow', message, func)

    def orange(self, message = None, func = True):
        return self.style('orange', message, func)

    def red(self, message = None, func = True):
        return self.style('red', message, func)

    def magenta(self, message = None, func = True):
        return self.style('magenta', message, func)

    def violet(self, message = None, func = True):
        return self.style('violet', message, func)

    def blue(self, message = None, func = True):
        return self.style('blue', message, func)

    def cyan(self, message = None, func = True):
        return self.style('cyan', message, func)

    def green(self, message = None, func = True):
        return self.style('green', message, func)


    def command_color(self, message = None, func = True):
        return self.style(settings.COMMAND_COLOR, message, func)

    def header_color(self, message = None, func = True):
        return self.style(settings.HEADER_COLOR, message, func)

    def key_color(self, message = None, func = True):
        return self.style(settings.KEY_COLOR, message, func)

    def value_color(self, message = None, func = True):
        return self.style(settings.VALUE_COLOR, message, func)

    def json_color(self, message = None, func = True):
        return self.style(settings.JSON_COLOR, message, func)

    def encrypted_color(self, message = None, func = True):
        return self.style(settings.ENCRYPTED_COLOR, message, func)

    def dynamic_color(self, message = None, func = True):
        return self.style(settings.DYNAMIC_COLOR, message, func)

    def relation_color(self, message = None, func = True):
        return self.style(settings.RELATION_COLOR, message, func)

    def prefix_color(self, message = None, func = True):
        return self.style(settings.PREFIX_COLOR, message, func)

    def success_color(self, message = None, func = True):
        return self.style(settings.SUCCESS_COLOR, message, func)

    def notice_color(self, message = None, func = True):
        return self.style(settings.NOTICE_COLOR, message, func)

    def warning_color(self, message = None, func = True):
        return self.style(settings.WARNING_COLOR, message, func)

    def error_color(self, message = None, func = True):
        return self.style(settings.ERROR_COLOR, message, func)

    def traceback_color(self, message = None, func = True):
        return self.style(settings.TRACEBACK_COLOR, message, func)
