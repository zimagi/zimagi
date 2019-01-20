from django.conf import settings
from django.core.management.base import CommandError
from django.utils.module_loading import import_string

from systems.command import base, args, messages
from systems.command.mixins import colors, command, data
from systems.api import client
from utility import display

import threading
import time
import logging


logger = logging.getLogger(__name__)


class ActionResult(object):

    def __init__(self, messages = []):
        self.stream = messages
        self.named = {}
        self.errors = []
        
        self.add(messages)


    @property
    def active_user(self):
        return self.get_named_data('active_user')


    def add(self, messages):
        if not isinstance(messages, (list, tuple)):
            messages = [messages]
        
        for msg in messages:
            self.stream.append(msg)

            if msg.name:
                self.named[msg.name] = msg

            if msg.type == 'ErrorMessage':
                self.errors.append(msg)


    @property
    def aborted(self):
        return len(self.errors) > 0

    def error_message(self):
        messages = []
        for msg in self.errors:
            messages.append(msg.format())
        
        return "\n".join(messages)


    def get_named_data(self, name):
        msg = self.named.get(name, None)
        if msg:
            return msg.data
        return None      


class ActionCommand(
    colors.ColorMixin,
    command.ExecMixin,
    data.EnvironmentMixin,
    data.UserMixin,
    data.ProjectMixin, 
    base.AppBaseCommand
):
    def __init__(self, stdout = None, stderr = None, no_color = False):
        super().__init__(stdout, stderr, no_color)


    def get_action_result(self, messages = []):
        return ActionResult(messages)


    def parse_base(self):
        super().parse_base()

        if not self.api_exec:
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
    def curr_env(self):
        return self.get_env()

    @property
    def active_user(self):
        if not getattr(self, '_active_user', None):
            self._active_user = self._user.active_user
        return self._active_user


    def confirm(self):
        # Override in subclass
        pass

    def _exec_wrapper(self):
        try: 
            if self.active_user:
                self.data("> active user", self.active_user.username, 'active_user')
                self.info('-----------------------------------------')
            
            self.exec()

        except Exception as e:
            if not isinstance(e, CommandError):
                self.error(e, 
                    terminate = False, 
                    traceback = display.format_exception_info()
                )        


    def exec(self):
        # Override in subclass
        pass

    def exec_remote(self, env, name, options = {}, display = True):
        result = self.get_action_result()
        command = self.find_command(name)

        def message_callback(data):
            msg = messages.AppMessage.get(data)
            msg.colorize = not self.no_color

            if display:
                msg.display()
            
            result.add(msg)

        api = client.API(env.host, env.port, env.token,
            params_callback = command.preprocess_handler, 
            message_callback = message_callback
        )
        api.execute(name, { 
            key: options[key] for key in options if key not in (
                'local',
                'debug',
                'no_color'
            )
        })
        command.postprocess_handler(result)

        if result.aborted:
            raise CommandError()

        return result


    def preprocess(self, params):
        # Override in subclass
        pass

    def preprocess_handler(self, params):
        self.preprocess(params)
    
    def postprocess(self, result):
        # Override in subclass
        pass

    def postprocess_handler(self, result):
        if not result.aborted:
            self.postprocess(result)


    def _init_exec(self, options):
        self.options.clear()
        self.messages.clear()
        
        for key, value in options.items():
            self.options.add(key, value)
        
        for facade in (self._state, self._env, self._config, self._user, self._token, self._user_group, self._project):
            if getattr(facade, 'ensure', None) and callable(facade.ensure):
                facade.ensure(self._env, self._user)


    def handle(self, *args, **options):
        env = self.curr_env

        self._init_exec(options)

        if not self.local and env and env.host and self.server_enabled() and self.remote_exec():
            self.data("> environment ({})".format(self.warning_color(env.host)), env.name)
            self.info('-----------------------------------------')

            self.confirm()
            self.exec_remote(env, self.get_full_name(), options, display = True)
        else:
            if env:
                self.data('> environment', env.name)
                self.info('-----------------------------------------')
            
            self.confirm()
            self.exec()
                

    def handle_api(self, options):
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


    def get_provider(self, type, name, *args, **options):
        return getattr(self, "_get_{}_provider".format(type))(name, *args, **options)
    

    def _get_compute_provider(self, type, server = None):
        try:
            if type not in settings.COMPUTE_PROVIDERS.keys() and type != 'help':
                raise Exception("Not supported")

            if type == 'help':
                return import_string('systems.compute.BaseComputeProvider')(type, self)

            return import_string(settings.COMPUTE_PROVIDERS[type])(type, self, 
                server = server
            )
        except Exception as e:
            self.error("Compute provider {} error: {}".format(type, e))


    def _get_storage_provider(self, type, storage = None):
        try:
            if type not in settings.STORAGE_PROVIDERS.keys() and type != 'help':
                raise Exception("Not supported")

            if type == 'help':
                return import_string('systems.storage.BaseStorageProvider')(type, self)

            return import_string(settings.STORAGE_PROVIDERS[type])(type, self, 
                storage = storage
            )
        except Exception as e:
            self.error("Storage provider {} error: {}".format(type, e))


    def _get_project_provider(self, type, project = None):
        try:
            if type not in settings.PROJECT_PROVIDERS.keys() and type != 'help':
                raise Exception("Not supported")

            if type == 'help':
                return import_string('systems.project.BaseProjectProvider')(type, self)

            return import_string(settings.PROJECT_PROVIDERS[type])(type, self, 
                project = project
            )
        except Exception as e:
            self.error("Project provider {} error: {}".format(type, e))


    def _get_task_provider(self, type, project, config):
        try:
            if type not in settings.TASK_PROVIDERS.keys() and type != 'help':
                raise Exception("Not supported")

            if type == 'help':
                return import_string('systems.task.BaseTaskProvider')(type, self)

            return import_string(settings.TASK_PROVIDERS[type])(type, self, project, config)
        
        except Exception as e:
            self.error("Task execution provider {} error: {}".format(type, e))
