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
    def active_user(self):
        if not getattr(self, '_active_user', None):
            self._active_user = self._user.active_user
        return self._active_user

    def check_access(self, *groups):
        user_groups = []

        for group in groups:
            if isinstance(group, (list, tuple)):
                user_groups.extend(list(group))
            else:
                user_groups.append(group)

        if self.active_user and len(user_groups):
            if not self.active_user.groups.filter(name__in=user_groups).exists():
                self.warning("Operation requires at least one of the following roles: {}".format(", ".join(user_groups)))
                return False
        
        return True


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

    def exec_local(self, name, options = {}):
        command = self.find_command(name)
        command.messages = self.messages

        command._init_options(options)
        command.exec()

    def exec_remote(self, env, name, options = {}, display = True):
        result = self.get_action_result()
        command = self.find_command(name)
        command.messages = self.messages
        
        def message_callback(data):
            msg = messages.AppMessage.get(data)
            msg.colorize = not self.no_color

            if display:
                msg.display()
            
            result.add(msg)
            command.messages.add(msg)

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
        self.messages.clear()

        for facade in (self._state, self._env, self._config, self._user, self._token, self._user_group, self._project):
            if getattr(facade, 'ensure', None) and callable(facade.ensure):
                facade.ensure(self._env, self._user)

    def _init_options(self, options):
        self.options.clear()
        
        for key, value in options.items():
            self.options.add(key, value)


    def handle(self, *args, **options):
        env = self.curr_env
        local = options.get('local', False)

        self._init_exec(options)    
                        
        if not local and env and env.host and self.server_enabled() and self.remote_exec():
            self.data("> environment ({})".format(self.warning_color(env.host)), env.name)
            self.info('=========================================')

            self.confirm()
            self.exec_remote(env, self.get_full_name(), options, display = True)
        else:
            if env:
                self.data('> environment', env.name)
                self.info('=========================================')

            self._init_options(options)
            self.confirm()
            self.exec()
                

    def handle_api(self, options):
        self._init_exec(options)
        self._init_options(options)

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
        type_components = type.split(':')
        type = type_components[0]
        subtype = type_components[1] if len(type_components) > 1 else None

        provider_map = {
            'project': {
                'registry': settings.PROJECT_PROVIDERS,
                'base': 'systems.project.BaseProjectProvider'
            },
            'task': {
                'registry': settings.TASK_PROVIDERS,
                'base': 'systems.task.BaseTaskProvider'
            },
            'network': {
                'registry': settings.NETWORK_PROVIDERS,
                'base': 'systems.network.BaseNetworkProvider'
            },
            'storage': {
                'registry': settings.STORAGE_PROVIDERS,
                'base': 'systems.storage.BaseStorageProvider'
            },
            'compute': {
                'registry': settings.COMPUTE_PROVIDERS,
                'base': 'systems.compute.BaseComputeProvider'
            }
        }
        provider_config = provider_map[type]['registry']
        base_provider = provider_map[type]['base']

        try:
            if name not in provider_config.keys() and name != 'help':
                raise Exception("Not supported")

            provider_class = provider_config[name] if name != 'help' else base_provider
            return import_string(provider_class)(name, self, *args, **options).context(subtype, self.test)
        
        except Exception as e:
            self.error("{} provider {} error: {}".format(type.title(), name, e))
