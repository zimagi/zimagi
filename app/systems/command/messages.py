from threading import Lock

from django.core.management.color import color_style

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
    

class AppMessage(object):

    def __init__(self, message = '', name = None):
        self.style = color_style()
        self.colorize = True

        self.type = self.__class__.__name__
        self.name = name
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
        
        return data

    def to_json(self):
        return json.dumps(self.render()) + "\n"


    def display(self):
        print(self.message)


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


class DataMessage(AppMessage):

    def __init__(self, message = '', data = None, name = None):
        super().__init__(message, name)
        self.data = data

    def render(self):
        result = super().render()
        result['data'] = self.data
        return result

    def display(self):
        print("{}: {}".format(
            self.message, 
            self.success_color(self.data)
        ))


class InfoMessage(AppMessage):
    pass


class NoticeMessage(AppMessage):

    def display(self):
        print(self.notice_color(self.message))


class SuccessMessage(AppMessage):

    def display(self):
        print(self.success_color(self.message))


class WarningMessage(AppMessage):

    def display(self):
        print(self.warning_color(self.message))


class ErrorMessage(AppMessage):

    def display(self):
        print(self.error_color(self.message))


class TableMessage(AppMessage):

    def display(self):
        print_table(self.message)
