from django.conf import settings
from django.core.management.base import CommandError

from systems.command import base, args, messages
from systems.command.mixins.colors import ColorMixin
from systems.command.mixins.data.user import UserMixin
from systems.command.mixins.data.environment import EnvironmentMixin
from systems.api import client
from systems import cloud
from utility import ssh

import sys
import subprocess
import threading
import time
import json
import logging


logger = logging.getLogger(__name__)


class ActionCommand(
    ColorMixin,
    EnvironmentMixin,
    UserMixin, 
    base.AppBaseCommand
):
    def __init__(self, stdout = None, stderr = None, no_color = False):
        super().__init__(stdout, stderr, no_color)


    def parse_base(self):
        super().parse_base()
        self.parse_local()


    def parse_local(self):
        name = 'local'
        help_text = "force command to run in local environment"

        self.add_schema_field(name, 
            args.parse_bool(self.parser, name, '--local', help_text), 
            True
        )

    @property
    def local(self):
        return self.options.get('local', False)


    @property
    def active_user(self):
        return self._user.active_user


    def confirm(self):
        # Override in subclass
        pass

    def _exec_wrapper(self):
        try: 
            if self.active_user:
                self.data("> active user", self.active_user.username)
            
            self.exec()

        except Exception as e:
            self.error(e)        

    def exec(self):
        # Override in subclass
        pass

    def _init_exec(self, options):
        self.messages.clear()
        
        for key, value in options.items():
            self.options.add(key, value)

        return self.get_env()        

    def handle(self, *args, **options):
        errors = []

        for facade in (self._state, self._env, self._user, self._token, self._user_group):
            if getattr(facade, 'ensure', None) and callable(facade.ensure):
                facade.ensure(self._env, self._user)
        
        env = self._init_exec(options)

        def message_callback(data):
            msg = messages.AppMessage.get(data)
            msg.colorize = not self.no_color
            msg.display()

            if msg.type == 'ErrorMessage':
                errors.append(msg)

            return msg.render()

        if not self.local and env and env.host and self.server_enabled():
            api = client.API(env.host, env.port, env.token, message_callback)
            
            self.data("> environment ({})".format(self.warning_color(env.host)), env.name)
            self.confirm()
            api.execute(self.get_full_name(), { 
                key: options[key] for key in options if key not in (
                    'no_color',
                )
            })
            if len(errors):
                raise CommandError()
        else:
            if env:
                self.data('> environment', env.name)
            
            self.confirm()
            self.exec()
                

    def handle_api(self, options):
        for facade in (self._state, self._env, self._user, self._token, self._user_group):
            if getattr(facade, 'ensure', None) and callable(facade.ensure):
                logger.info("Ensuring resources for: {}".format(facade.name))
                facade.ensure(self._env, self._user)
        
        self._init_exec(options)

        action = threading.Thread(target = self._exec_wrapper)
        action.start()
        
        while True:
            time.sleep(0.25)
            logger.debug("Checking messages")

            while True:
                msg = self.messages.process()
                if msg:
                    message = msg.to_json()
                    logger.info("Processing message: {}".format(message))
                    yield message
                else:
                    logger.debug("No more messages to process")
                    break

            if not action.is_alive():
                logger.debug("Command thread is no longer active")
                break


    def sh(self, command_str, input = None):
        process = subprocess.Popen(command_str,
                                   shell = True,
                                   stdin = subprocess.PIPE,
                                   stdout = subprocess.PIPE,
                                   stderr = subprocess.PIPE)
    
        if input:
            if isinstance(input, (list, tuple)):
                input = "\n".join(input) + "\n"
            else:
                input = input + "\n"

            stdoutdata, stderrdata = process.communicate(input = str.encode(input))
        else:
            stdoutdata, stderrdata = process.communicate()    

        return {
            'stdout': stdoutdata.decode("utf-8"), 
            'stderr': stderrdata.decode("utf-8"), 
            'status': process.returncode
        }

    def ssh(self, hostname, username, password = None, key = None):
        try:
            conn = ssh.SSH(hostname, username, password, key, self._ssh_callback)
            conn.wrap_exec(self._ssh_exec)
            conn.wrap_file(self._ssh_file)
        except Exception as e:
            self.error("SSH connection to {} failed: {}".format(hostname, e))
        
        return conn

    def _ssh_exec(self, ssh, executer, command, args, options):
        id_prefix = "[{}]".format(ssh.hostname)

        try:
            return executer(command, args, options)
        except Exception as e:
            self.error("SSH {} execution failed: {}".format(command, e), prefix = id_prefix)

    def _ssh_file(self, ssh, executer, callback, *args):
        id_prefix = "[{}]".format(ssh.hostname)

        try:
            executer(callback, *args)
        except Exception as e:
            self.error("SFTP transfer failed: {}".format(e), prefix = id_prefix)

    def _ssh_callback(self, ssh, stdin, stdout, stderr):
        id_prefix = "[{}]".format(ssh.hostname)

        def stream_stdout():
            for line in stdout:
                self.info(line.strip('\n'), prefix = id_prefix)

        def stream_stderr():
            for line in stderr:
                if not line.startswith('[sudo]'):
                    self.warning(line.strip('\n'), prefix = id_prefix)

        thrd_out = threading.Thread(target = stream_stdout)
        thrd_out.start()

        thrd_err = threading.Thread(target = stream_stderr)
        thrd_err.start()

        thrd_out.join()
        thrd_err.join()


    def cloud(self, type):
        try:
            if type not in settings.CLOUD_PROVIDERS.keys():
                raise Exception("Not supported")

            return getattr(cloud, settings.CLOUD_PROVIDERS[type])()
        
        except Exception as e:
            self.error("Cloud provider {} error: {}".format(type, e))
