from threading import Lock

from django.core.management.color import color_style

from systems.command import mixins
from utility.display import print_table

import json


class MessageQueue(object):

    def __init__(self):
        self.message_lock = Lock()
        self.messages = []

    def count(self):
        with self.message_lock:
            return len(self.messages)

    def add(self, msg):
        with self.message_lock:
            self.messages.append(msg)

    def process(self):
        msg = None

        with self.message_lock:
            if len(self.messages):
                msg = self.messages.pop(0)
        
        return msg

    def clear(self):
        with self.message_lock:
            self.messages = []
    

class AppMessage(mixins.ColorMixin):

    def __init__(self, message = '', name = None, prefix = None):
        self.style = color_style()
        self.colorize = True

        self.type = self.__class__.__name__
        self.name = name
        self.prefix = prefix
        self.message = message
    
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
        
        return data

    def to_json(self):
        return json.dumps(self.render()) + "\n"


    def display(self):
        print("{}{}".format(self._format_prefix(), self.message))

    def _format_prefix(self):
        if self.prefix:
            return self.warning_color(self.prefix) + ' '
        else:
            return ''


class DataMessage(AppMessage):

    def __init__(self, message = '', data = None, name = None, prefix = None):
        super().__init__(message, name, prefix)
        self.data = data

    def render(self):
        result = super().render()
        result['data'] = self.data
        return result

    def display(self):
        print("{}{}: {}".format(
            self._format_prefix(),
            self.message, 
            self.success_color(self.data)
        ))


class InfoMessage(AppMessage):
    pass


class NoticeMessage(AppMessage):

    def display(self):
        print("{}{}".format(self._format_prefix(), self.notice_color(self.message)))


class SuccessMessage(AppMessage):

    def display(self):
        print("{}{}".format(self._format_prefix(), self.success_color(self.message)))


class WarningMessage(AppMessage):

    def display(self):
        print("{}{}".format(self._format_prefix(), self.warning_color(self.message)))


class ErrorMessage(AppMessage):

    def display(self):
        print("{}{}".format(self._format_prefix(), self.error_color(self.message)))


class TableMessage(AppMessage):

    def display(self):
        print_table(self.message, self._format_prefix())
