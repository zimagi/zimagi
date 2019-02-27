from django.core.management.color import color_style, no_style

from utility.config import RuntimeConfig


class ColorMixin(object):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, *kwargs)
        self.set_color_style()
        

    def set_color_style(self):
        if RuntimeConfig.color():
            self.style = color_style()
        else:
            self.style = no_style()    


    def success_color(self, message):
        if RuntimeConfig.color():
            return self.style.SUCCESS(message)
        return message

    def notice_color(self, message):
        if RuntimeConfig.color():
            return self.style.NOTICE(message)
        return message

    def warning_color(self, message):
        if RuntimeConfig.color():
            return self.style.WARNING(message)
        return message

    def error_color(self, message):
        if RuntimeConfig.color():
            return self.style.ERROR(message)
        return message
