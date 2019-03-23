from collections import OrderedDict

from django.core.management.base import CommandError
from django.utils.module_loading import import_string

from settings.config import Config
from utility.data import ensure_list
from utility.shell import Shell
from utility.temp import temp_dir

import os
import sys
import time
import datetime
import re
import pathlib
import shutil
import importlib
import json
import yaml
import docker


class RequirementError(Exception):
    pass


class Manager(object):

    def __init__(self, app_dir, data_dir, runtime_path, module_base_dir, default_env):
        self.client = docker.from_env()
        self.app_dir = app_dir
        self.data_dir = data_dir
        self.config = Config.load(runtime_path, {})
        self.env = self.config.get('CENV_ENV', default_env)
        self.module_dir = os.path.join(module_base_dir, self.env)
        self.modules = {}
        self.ordered_modules = None
        self.plugins = {}
        self.reload()

    def reload(self):
        pathlib.Path(self.module_dir).mkdir(mode = 0o700, parents = True, exist_ok = True)

        self.module_config(self.app_dir)
        self.update_search_path()
        self.collect_environment()
        self.load_plugins()


    def load_file(self, file_path):
        content = None
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                content = file.read()
        return content

    def load_yaml(self, file_path):
        content = self.load_file(file_path)
        if content:
            content = yaml.safe_load(content)
        return content

    def load_env(self, env_name, variables = {}):
        env_file = os.path.join(self.data_dir, "{}.env".format(env_name))
        return Config.load(env_file, {})


    def module_config(self, path):
        if path not in self.modules:
            cenv_file = os.path.join(path, 'cenv.yml')
            self.modules[path] = self.load_yaml(cenv_file)
        return self.modules[path]

    def module_lib_dir(self, path):
        config = self.module_config(path)
        lib_dir = False

        if 'lib' in config:
            lib_dir = config['lib']
            if not lib_dir:
                return False
            elif lib_dir == '.':
                lib_dir = False

        return os.path.join(path, lib_dir) if lib_dir else path

    def get_modules(self):
        if not self.ordered_modules:
            self.ordered_modules = OrderedDict()
            self.ordered_modules[self.app_dir] = self.module_config(self.app_dir)

            modules = {}
            for name in os.listdir(self.module_dir):
                path = os.path.join(self.module_dir, name)
                if os.path.isdir(path):
                    modules[name] = self.module_config(path)

            def process(name, config):
                if 'modules' in config:
                    for parent in config['modules'].keys():
                        if parent in modules:
                            process(parent, modules[parent])

                path = os.path.join(self.module_dir, name)
                self.ordered_modules[path] = config

            for name, config in modules.items():
                process(name, config)

        return self.ordered_modules

    def get_module_libs(self, include_core = True):
        module_libs = OrderedDict()
        for path, config in self.get_modules().items():
            if include_core or path != self.app_dir:
                lib_dir = self.module_lib_dir(path)
                if lib_dir:
                    module_libs[lib_dir] = config
        return module_libs


    def update_search_path(self):
        for lib_dir in self.get_module_libs().keys():
            sys.path.append(lib_dir)
        importlib.invalidate_caches()


    def module_dirs(self, sub_dir = None, include_core = True):
        module_dirs = []
        for lib_dir in self.get_module_libs(include_core).keys():
            if sub_dir:
                abs_sub_dir = os.path.join(lib_dir, sub_dir)
                if os.path.isdir(abs_sub_dir):
                    module_dirs.append(abs_sub_dir)
            else:
                module_dirs.append(lib_dir)
        return module_dirs

    def module_file(self, *path_components):
        module_file = None

        for module_dir in self.module_dirs():
            path = os.path.join(module_dir, *path_components)
            if os.path.isfile(path):
                module_file = path

        if not module_file:
            raise RequirementError("Module file {} not found".format("/".join(path_components)))
        return module_file

    def help_search_path(self):
        return self.module_dirs('help')

    def settings_modules(self):
        modules = []
        for module_dir in self.module_dirs(None, False):
            settings_dir = os.path.join(module_dir, 'settings')

            if os.path.isdir(settings_dir):
                for name in os.listdir(settings_dir):
                    if name[0] != '_':
                        try:
                            module = "settings.{}".format(name.replace('.py', ''))
                            modules.append(importlib.import_module(module))
                        except Exception as e:
                            shutil.rmtree(module_dir, ignore_errors = True)
                            raise e
        return modules


    def installed_apps(self):
        apps = []
        for module_dir in self.module_dirs():
            data_dir = os.path.join(module_dir, 'data')
            interface_dir = os.path.join(module_dir, 'interface')

            if os.path.isdir(interface_dir):
                for name in os.listdir(interface_dir):
                    if name[0] != '_':
                        apps.append("interface.{}".format(name))

            if os.path.isdir(data_dir):
                for name in os.listdir(data_dir):
                    if name[0] != '_':
                        apps.append("data.{}".format(name))
        return apps

    def installed_middleware(self):
        middleware = []
        for middleware_dir in self.module_dirs('middleware'):
            for name in os.listdir(middleware_dir):
                if name[0] != '_':
                    middleware.append("middleware.{}.Middleware".format(name))
        return middleware


    def collect_environment(self):
        for path, config in self.get_modules().items():
            if 'env' in config:
                for variable, value in config['env'].items():
                    os.environ[variable] = str(value)


    def install_scripts(self, command, display = True):
        for path, config in self.get_modules().items():
            if 'scripts' in config:
                for script_path in ensure_list(config['scripts']):
                    script_path = os.path.join(path, script_path)

                    if os.path.isfile(script_path):
                        with temp_dir() as temp:
                            if display:
                                command.info("Executing script: {}".format(script_path))

                            pathlib.Path(script_path).chmod(0o700)
                            if not command.sh([ script_path ],
                                cwd = temp.temp_path,
                                env = { 'MODULE_DIR': path },
                                display = display
                            ):
                                command.error("Installation script failed: {}".format(script_path))


    def parse_requirements(self):
        requirements = []
        for path, config in self.get_modules().items():
            if 'requirements' in config:
                for requirement_path in ensure_list(config['requirements']):
                    requirement_path = os.path.join(path, requirement_path)
                    file_contents = self.load_file(requirement_path)
                    if file_contents:
                        requirements.extend([ req for req in file_contents.split("\n") if req and req[0].strip() != '#' ])
        return requirements

    def install_requirements(self, command, display = True):
        req_map = {}
        for req in self.parse_requirements():
            # PEP 508
            req_map[re.split(r'[\>\<\!\=\~\s]+', req)[0]] = req

        requirements = list(req_map.values())

        if len(requirements):
            req_text = "\n> ".join(requirements)
            if display:
                command.info("Installing Python requirements:\n> {}".format(req_text))

            if not command.sh(['pip3', 'install'] + requirements, display = display):
                if display:
                    command.error("Installation of requirements failed")
                else:
                    command.error("Installation of requirements failed:\n> {}".format(req_text))


    def load_plugins(self):
        self.plugins = {}
        for plugin_dir in self.module_dirs('plugins'):
            for type in os.listdir(plugin_dir):
                if type[0] != '_':
                    provider_dir = os.path.join(plugin_dir, type)
                    base_module = "plugins.{}".format(type)
                    base_class = "{}.base.BaseProvider".format(base_module)

                    if type not in self.plugins:
                        self.plugins[type] = {
                            'base': base_class,
                            'providers': {}
                        }
                    for name in os.listdir(provider_dir):
                        if name[0] != '_' and name != 'base.py' and name.endswith('.py'):
                            name = name.strip('.py')
                            provider_class = "{}.{}.Provider".format(base_module, name)
                            self.plugins[type]['providers'][name] = provider_class

    def provider_base(self, type):
        return self.plugins[type]['base']

    def providers(self, type, include_system = False):
        providers = {}
        for name, class_name in self.plugins[type]['providers'].items():
            if include_system or not name.startswith('sys_'):
                providers[name] = class_name
        return providers


    def load_roles(self):
        roles = {}
        for path, config in self.get_modules().items():
            if 'roles' in config:
                for name, description in config['roles'].items():
                    roles[name] = description
        return roles


    def load_config_provisioner(self, profile):
        return import_string("provisioners.config.Provisioner")(
            'config',
            profile
        )

    def load_provisioners(self, profile):
        provisioners = {}
        for provisioner_dir in self.module_dirs('provisioners'):
            for type in os.listdir(provisioner_dir):
                if type[0] != '_' and type.endswith('.py'):
                    name = type.replace('.py', '')

                    if name != 'config':
                        provisioner_class = "provisioners.{}.Provisioner".format(name)
                        instance = import_string(provisioner_class)(name, profile)
                        priority = instance.priority()

                        if priority not in provisioners:
                            provisioners[priority] = [ instance ]
                        else:
                            provisioners[priority].append(instance)
        return provisioners


    def service_file(self, name):
        directory = os.path.join(self.data_dir, 'run')
        pathlib.Path(directory).mkdir(mode = 0o700, parents = True, exist_ok = True)
        return os.path.join(directory, "{}.data".format(name))

    def save_service(self, command, name, id, data = {}):
        data['id'] = id
        with open(self.service_file(name), 'w') as file:
            file.write(json.dumps(data))

    def get_service(self, command, name, wait = 10):
        service_file = self.service_file(name)
        if os.path.isfile(service_file):
            with open(self.service_file(name), 'r') as file:
                data = json.loads(file.read())
                service = self.service_container(data['id'])
                if service:
                    if service.status != 'running':
                        service.start()
                        success, service = self.check_service(command, name, service, wait)
                        if not success:
                            self.service_error(command, name, service)

                    data['ports'] = service.attrs["NetworkSettings"]["Ports"]
                    return data
                else:
                    self.delete_service(command, name)
        return None

    def delete_service(self, command, name):
        os.remove(self.service_file(name))


    @property
    def container_id(self):
        return Shell.capture(('cat', '/proc/1/cpuset')).split('/')[-1]


    def generate_image_name(self, base_image):
        repository = base_image.split(':')[0]
        time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        return "{}:{}".format(repository, time)

    def create_image(self, id, image_name):
        container = self.service_container(id)
        if container:
            container.commit(image_name)


    def create_volume(self, name):
        return docker.from_env().volumes.create(name)


    def service_container(self, id):
        try:
            return self.client.containers.get(id)
        except docker.errors.NotFound:
            return None

    def start_service(self, command, name, image, ports,
        docker_entrypoint = None,
        docker_command = None,
        environment = {},
        volumes = {},
        memory = '250m',
        wait = 30
    ):
        data = self.get_service(command, name, wait)
        if data:
            if self.service_container(data['id']):
                if command:
                    command.notice("Service {} is already running".format(name))
                return

        for local_path, remote_config in volumes.items():
            if local_path[0] != '/':
                self.create_volume(local_path)

        service = self.client.containers.run(image,
            entrypoint = docker_entrypoint,
            command = docker_command,
            name = name,
            detach = True,
            restart_policy = {
                'Name': 'always',
            },
            mem_limit = memory,
            ports = ports,
            volumes = volumes,
            environment = environment
        )
        success, service = self.check_service(command, name, service, wait)
        self.save_service(command, name, service.id, {
            'image': image,
            'environment': environment,
            'volumes': volumes,
            'success': success
        })
        if not success:
            self.service_error(command, name, service)


    def check_service(self, command, name, service, wait = 30):
        success = True

        for index in range(wait):
            service = self.client.containers.get(service.id)
            if service.status == 'restarting':
                success = False
                break
            time.sleep(1)

        return (success, service)

    def service_error(self, command, name, service):
        error_message = "Service {} terminated with errors".format(name)
        log_message = service.logs().decode("utf-8").strip()

        if command:
            command.info(command.notice_color(log_message))

        self.stop_service(command, name, True)

        if command:
            command.error(error_message)
        else:
            raise CommandError("{}\n\n{}".format(error_message, log_message))


    def stop_service(self, command, name, remove = False):
        data = self.get_service(command, name)
        if data:
            container = self.client.containers.get(
                data['id']
            )
            container.stop()

            if remove:
                container.remove()
                self.delete_service(command, name)
        else:
            command.notice("Service {} is not running".format(name))
