
class ColorMixin(object):

    def success_color(self, message):
        if self.colorize:
            return self.style.SUCCESS(message)
        return message

    def notice_color(self, message):
        if self.colorize:
            return self.style.NOTICE(message)
        return message

    def warning_color(self, message):
        if self.colorize:
            return self.style.WARNING(message)
        return message

    def error_color(self, message):
        if self.colorize:
            return self.style.ERROR(message)
        return message
