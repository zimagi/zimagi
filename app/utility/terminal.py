import re
import sys
from zoneinfo import ZoneInfo

import colorful
from django.conf import settings


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


class TerminalMixin:
    def exit(self, code=0):
        sys.exit(code)

    def format_time(self, date_time, format="%Y-%m-%d %I:%M:%S %p"):
        return date_time.astimezone(ZoneInfo(getattr(settings, "TIME_ZONE", "UTC"))).strftime(format)

    def print(self, message="", stream=sys.stdout):
        def print_message():
            plain_text = self.raw_text(message)

            try:
                use_color = settings.MANAGER.runtime.color()
            except AttributeError:
                use_color = settings.DISPLAY_COLOR

            if use_color and plain_text != message:
                try:
                    colorful.print(message, file=stream)
                except Exception:
                    stream.write(plain_text + "\n")
            else:
                stream.write(plain_text + "\n")

        if getattr(settings, "DISPLAY_LOCK", None):
            with settings.DISPLAY_LOCK:
                print_message()
        else:
            print_message()

    def raw_text(self, message):
        if isinstance(message, str):
            message = re.sub(r"\{c\.[^\}]+\}", "", message)
        return message

    def style(self, style, message=None):
        def _format(output):
            try:
                use_color = settings.MANAGER.runtime.color()
            except AttributeError:
                use_color = settings.DISPLAY_COLOR

            if style and use_color:
                output = re.sub(r"([\{\}])", r"\1\1", str(output))
                lines = []
                for line in output.split("\n"):
                    lines.append("{c." + style + "}" + line + "{c.reset}")
                return "\n".join(lines)
            else:
                return output

        return _format(str(message)) if message is not None else ""

    def yellow(self, message=None):
        return self.style("yellow", message)

    def orange(self, message=None):
        return self.style("orange", message)

    def red(self, message=None):
        return self.style("red", message)

    def magenta(self, message=None):
        return self.style("magenta", message)

    def violet(self, message=None):
        return self.style("violet", message)

    def blue(self, message=None):
        return self.style("blue", message)

    def cyan(self, message=None):
        return self.style("cyan", message)

    def green(self, message=None):
        return self.style("green", message)

    def command_color(self, message=None):
        return self.style(getattr(settings, "COMMAND_COLOR", None), message)

    def header_color(self, message=None):
        return self.style(getattr(settings, "HEADER_COLOR", None), message)

    def key_color(self, message=None):
        return self.style(getattr(settings, "KEY_COLOR", None), message)

    def value_color(self, message=None):
        return self.style(getattr(settings, "VALUE_COLOR", None), message)

    def json_color(self, message=None):
        return self.style(getattr(settings, "JSON_COLOR", None), message)

    def dynamic_color(self, message=None):
        return self.style(getattr(settings, "DYNAMIC_COLOR", None), message)

    def relation_color(self, message=None):
        return self.style(getattr(settings, "RELATION_COLOR", None), message)

    def prefix_color(self, message=None):
        return self.style(getattr(settings, "PREFIX_COLOR", None), message)

    def success_color(self, message=None):
        return self.style(getattr(settings, "SUCCESS_COLOR", None), message)

    def notice_color(self, message=None):
        return self.style(getattr(settings, "NOTICE_COLOR", None), message)

    def warning_color(self, message=None):
        return self.style(getattr(settings, "WARNING_COLOR", None), message)

    def error_color(self, message=None):
        return self.style(getattr(settings, "ERROR_COLOR", None), message)

    def traceback_color(self, message=None):
        return self.style(getattr(settings, "TRACEBACK_COLOR", None), message)
