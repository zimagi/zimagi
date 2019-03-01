from django.conf import settings
from django.core.management.base import CommandError
from django.utils.module_loading import import_string

from systems.command import base, args, messages
from systems.command.mixins import command, data
from systems.api import client
from utility.config import RuntimeConfig
from utility import display

import multiprocessing
import threading
import time
import logging
import copy


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
    command.ExecMixin,
    data.LogMixin,
    data.ProjectMixin, 
    base.AppBaseCommand
):
    def get_action_result(self, messages = []):
        return ActionResult(messages)


    def parse_base(self):
        super().parse_base()

        if not RuntimeConfig.api():
            self.parse_local()


    def parse_local(self):
        self.parse_flag('local', '--local', "force command to run in local environment")

    @property
    def local(self):
        return self.options.get('local', False)


    @property
    def active_user(self):
        return self._user.active_user

    def check_access(self, *groups):
        user_groups = []

        for group in groups:
            if isinstance(group, (list, tuple)):
                user_groups.extend(list(group))
            else:
                user_groups.append(group)

        if len(user_groups):
            if not self.active_user.env_groups.filter(name__in=user_groups).exists():
                self.warning("Operation requires at least one of the following roles in environment: {}".format(", ".join(user_groups)))
                return False
        
        return True


    def confirm(self):
        # Override in subclass
        pass

    def _exec_wrapper(self):
        try: 
            self.data("> active user", self.active_user.name, 'active_user')
            self.info('-----------------------------------------')
            self.exec()

        except Exception as e:
            if not isinstance(e, CommandError):
                self.error(e, 
                    terminate = False, 
                    traceback = display.format_exception_info()
                )
        finally:
            self.flush()        


    def exec(self):
        # Override in subclass
        pass

    def exec_local(self, name, options = {}):
        command = base.find_command(name)
        command.parent_messages = self.messages
        success = True

        options = command.format_fields(copy.deepcopy(options))
        command._init_options(options)

        log_entry = self.log_exec(name, command.options.export())
        try:
            command.exec()            
        except Exception as e:
            success = False
            raise e
        finally:
            log_entry.messages = command.get_messages(True)
            log_entry.set_status(success)
            log_entry.save()

    def exec_remote(self, env, name, options = {}, display = True):
        result = self.get_action_result()
        command = base.find_command(name)
        command.parent_messages = self.messages
        success = True

        options = { 
            key: options[key] for key in options if key not in (
                'local',
                'no_color',
                'version'
            )
        }
        log_entry = self.log_exec(name, options)
        
        def message_callback(data):
            msg = self.create_message(data, decrypt = True)

            if display:
                msg.display()
            
            result.add(msg)
            command.queue(msg)

        try:
            api = client.API(env.host, env.port, env.user, env.token,
                params_callback = command.preprocess_handler, 
                message_callback = message_callback
            )
            api.execute(name, options)
            command.postprocess_handler(result)
            
            if result.aborted:
                success = False
                raise CommandError()
        finally:
            log_entry.messages = command.get_messages(True)
            log_entry.set_status(success)
            log_entry.save()
        
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


    def _init_exec(self):
        for facade_index_name in sorted(self.facade_index.keys()):
            self.facade_index[facade_index_name].ensure(self)        
        return self.get_env()

    def _init_options(self, options):
        self.options.clear()
        for key, value in options.items():
            self.options.add(key, value)


    def handle(self, options):
        env = self._init_exec()
        self._init_options(options)
                               
        if not self.local and env and env.host and self.server_enabled() and self.remote_exec():
            self.data("> environment ({})".format(self.warning_color(env.host)), env.name)
            self.info('=========================================')

            self.confirm()
            self.exec_remote(env, self.get_full_name(), options, display = True)
        else:
            if env:
                self.data('> environment', env.name)
                self.info('=========================================')

            self.confirm()

            success = True
            log_entry = self.log_exec(
                self.get_full_name(),
                self.options.export()
            )
            try:
                self.exec()
            except Exception as e:
                success = False
                raise e
            finally:
                log_entry.messages = self.get_messages(True)
                log_entry.set_status(success)
                log_entry.save()
               

    def handle_api(self, options):
        env = self._init_exec()
        self._init_options(options)
        
        success = True
        log_entry = self.log_exec(
            self.get_full_name(),
            self.options.export()
        )
        action = threading.Thread(target = self._exec_wrapper)
        action.start()
        
        while True:
            time.sleep(0.25)
            logger.debug("Checking messages")

            for data in iter(self.messages.get, None):
                log_entry.messages.append(data)

                msg = self.create_message(data, decrypt = False)
                if isinstance(msg, messages.ErrorMessage):
                    success = False
                
                package = msg.to_package()
                logger.debug("Processing message: {}".format(package))
                yield package

            if not action.is_alive():
                logger.debug("Command thread is no longer active")
                break
        
        log_entry.set_status(success)
        log_entry.save()


    def get_provider(self, type, name, *args, **options):
        type_components = type.split(':')
        type = type_components[0]
        subtype = type_components[1] if len(type_components) > 1 else None

        provider_map = {
            'user': {
                'registry': settings.USER_PROVIDERS,
                'base': 'systems.user.BaseUserProvider'
            },
            'env': {
                'registry': settings.ENVIRONMENT_PROVIDERS,
                'base': 'systems.environment.BaseEnvironmentProvider'
            },
            'group': {
                'registry': settings.GROUP_PROVIDERS,
                'base': 'systems.group.BaseGroupProvider'
            },
            'config': {
                'registry': settings.CONFIG_PROVIDERS,
                'base': 'systems.config.BaseConfigProvider'
            },
            'project': {
                'registry': settings.PROJECT_PROVIDERS,
                'base': 'systems.project.BaseProjectProvider'
            },
            'task': {
                'registry': settings.TASK_PROVIDERS,
                'base': 'systems.task.BaseTaskProvider'
            },
            'federation': {
                'registry': settings.FEDERATION_PROVIDERS,
                'base': 'systems.federation.BaseFederationProvider'
            },
            'network': {
                'registry': settings.NETWORK_PROVIDERS,
                'base': 'systems.network.BaseNetworkProvider'
            },
            'storage': {
                'registry': settings.STORAGE_PROVIDERS,
                'base': 'systems.storage.BaseStorageProvider'
            },
            'server': {
                'registry': settings.SERVER_PROVIDERS,
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
