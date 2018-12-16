from django.conf import settings
from django.core.management.base import CommandError

from systems.command import base
from systems.command import messages as command_messages
from systems.command.mixins.data.environment import EnvironmentMixin
from systems.api import client

import sys
import threading
import queue

import sh
import time


class ActionThread(threading.Thread):

    def __init__(self, action_callable, queue):
        super().__init__()
        self.exceptions = queue
        self.action = action_callable

    def run(self):
        try:
            self.action()
        except Exception:
            self.exceptions.put(sys.exc_info())


class ActionCommand(
    EnvironmentMixin, 
    base.AppBaseCommand
):
    def __init__(self, stdout = None, stderr = None, no_color = False):
        super().__init__(stdout, stderr, no_color)
        self.sh = sh


    def confirm(self):
        # Override in subclass
        pass

    def exec(self):
        # Override in subclass
        pass

    def _init_exec(self, options):
        self.options = options
        self.messages.clear()

        return self.get_env()        

    def handle(self, *args, **options):
        env = self._init_exec(options)
        errors = []

        def message_callback(data):
            msg = getattr(command_messages, data['type'])()
            msg.colorize = not self.no_color
            msg.load(data)
            msg.display()

            if msg.type == 'ErrorMessage':
                errors.append(msg)

        if env and env.host and self.server_enabled():
            api = client.API(env.host, env.port, env.token, message_callback)
            
            self.data("> Environment", env.name)
            self.confirm()
            api.execute(self.get_full_name(), { 
                key: options[key] for key in options if key not in (
                    'no_color',
                )
            })
            if len(errors):
                raise CommandError()
        else:
            self.confirm()
            self.exec()
                

    def handle_api(self, options):
        env = self._init_exec(options)
        
        errors = queue.Queue()
        action = ActionThread(self.exec, errors)
        action.start()
        
        while True:
            time.sleep(0.25)

            while True:
                msg = self.messages.process()
                if msg:
                    yield msg.to_json()
                else:
                    break
            
            if not action.is_alive():
                break
