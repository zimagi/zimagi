from utility.text import Template
from utility.shell import Shell
from utility.parallel import Parallel
from utility.filesystem import load_file, save_file, remove_file
from utility.data import ensure_list, normalize_value, dependents, prioritize, dump_json, load_json

import os
import docker
import subprocess
import pathlib
import copy
import re
import time
import datetime
import logging


logger = logging.getLogger(__name__)


class ServiceError(Exception):
    pass


class ManagerServiceMixin(object):

    def __init__(self):
        super().__init__()

        self.client = None
        try:
            self.client = docker.from_env()
        except Exception as error:
            pass


    @property
    def container_id(self):
        matches = re.search(
            r'/var/lib/docker/containers/([^\/]+)/hostname',
            Shell.capture(('cat', '/proc/self/mountinfo'))
        )
        if not matches:
            raise ServiceError("Container id for service not found")
        return matches[1]


    def _service_container(self, id):
        if self.client:
            try:
                return self.client.containers.get(id)
            except docker.errors.NotFound:
                pass

        return None


    def generate_image_name(self, base_image, tag = None):
        image = base_image.split(':')[0]
        if tag is None:
            tag = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        return "{}:{}".format(image, tag)


    def list_images(self):
        if self.client:
            return self.client.images.list()
        return []

    def create_image(self, id, image_name):
        container = self._service_container(id)
        if container:
            container.commit(image_name)

    def delete_image(self, image_name, force = True, noprune = False):
        if self.client:
            image = self.client.images.get(image_name)
            self.client.images.remove(image.id, force = force, noprune = noprune)


    def _get_network(self, name):
        if self.client:
            try:
                return self.client.networks.get(name)
            except docker.errors.NotFound:
                return self.client.networks.create(name, driver = 'bridge')
        return None

    def _get_volume(self, name):
        if self.client:
            try:
                return self.client.volumes.get(name)
            except docker.errors.NotFound:
                return self.client.volumes.create(name)
        return None


    def _normalize_name(self, name):
        if isinstance(name, (list, tuple)):
            return [ "{}-{}-{}".format(self.app_name, item, self.env.name) for item in name ]
        return "{}-{}-{}".format(self.app_name, name, self.env.name)


    @property
    def service_names(self):
        return list(self.get_spec('services').keys())


    def get_service_spec(self, name, services = None):
        if services is None:
            services = self.get_spec('services')

        environment = {
            'ZIMAGI_ENV_NAME': self.env.name,
            'ZIMAGI_APP_NAME': self.app_name,
            'ZIMAGI_CLI_EXEC': False
        }
        service = copy.deepcopy(services[name])

        for env_name, value in dict(os.environ).items():
            if env_name.startswith('ZIMAGI_') and not env_name.endswith('_EXEC'):
                environment[env_name] = value

        def interpolate(data, variables):
            if isinstance(data, dict):
                generated = {}
                for key, value in data.items():
                    key = interpolate(key, variables)
                    if key is not None:
                        generated[key] = interpolate(value, variables)
                data = generated
            elif isinstance(data, (list, tuple)):
                generated = []
                for value in data:
                    value = interpolate(value, variables)
                    if value is not None:
                        generated.append(value)
                data = generated
            elif isinstance(data, str):
                parser = Template(data)
                data = normalize_value(parser.substitute(**variables).strip())
                data = None if not data else data
            return data

        service = interpolate(service, environment)
        inherit_environment = service.pop('inherit_environment', False)
        if inherit_environment:
            service['environment'] = { **environment, **service['environment'] }
        return service


    def initialize_services(self, names = None):
        if self.client and names:
            services = self.get_spec('services')
            names = dependents(services, ensure_list(names))

            def start_service(service_name):
                if service_name in names:
                    service_spec = self.get_service_spec(service_name, services = services)
                    self.start_service(service_name, **service_spec)

            for priority, service_names in sorted(prioritize(services, False).items()):
                results = Parallel.list(service_names, start_service)
                if results.aborted:
                    raise ServiceError("\n".join([ str(error) for error in results.errors ]))


    def _service_file(self, name):
        name = self._normalize_name(name)
        directory = os.path.join(self.data_dir, 'run')
        pathlib.Path(directory).mkdir(parents = True, exist_ok = True)
        return os.path.join(directory, "{}.data".format(name))

    def _save_service(self, name, id, data = None):
        if not data:
            data = {}

        data['id'] = id
        save_file(self._service_file(name), dump_json(data, indent = 2))

    def get_service(self, name, restart = True, create = True):
        if not self.client:
            return None

        service_file = self._service_file(name)
        services = self.get_spec('services')

        for dependent in dependents(services, [ name ]):
            if dependent != name:
                dependent_data = self.get_service(dependent,
                    restart = restart,
                    create = create
                )
                if not dependent_data:
                    return None

        service_spec = self.get_service_spec(name)

        if os.path.isfile(service_file):
            data = load_json(load_file(service_file))
            service = self._service_container(data['id'])
            if not service and create:
                service_id = self.start_service(name, **service_spec)
                service = self._service_container(service_id)
            if service:
                if service.status != 'running':
                    if create or restart:
                        self.print("{} {}".format(
                            self.notice_color('Restarting Zimagi service'),
                            self.key_color(name)
                        ))
                        service.start()
                        success, service = self._check_service(name, service)
                        if not success:
                            self._service_error(name, service)
                    else:
                        return None

                data['service'] = service
                data['ports'] = {}
                for port_name, port_list in service.attrs['NetworkSettings']['Ports'].items():
                    if port_list:
                        for port in port_list:
                            if port['HostIp'] == '0.0.0.0':
                                data['ports'][port_name] = int(port['HostPort'])
                                break
                return data

            elif create:
                raise ServiceError("Zimagi could not initialize and load service {}".format(name))
        elif create:
            self.start_service(name, **service_spec)
            return self.get_service(name)
        return None

    def _check_service(self, name, service):
        spec = self.get_service_spec(name)
        start_time = time.time()
        current_time = start_time
        success = True

        while (current_time - start_time) <= spec.get('wait', 30):
            service = self.client.containers.get(service.id)
            if service.status != 'running':
                success = False
                break

            time.sleep(0.1)
            current_time = time.time()

        return (success, service)

    def _delete_service(self, name):
        remove_file(self._service_file(name))


    def start_service(self, name, image,
        ports = None,
        entrypoint = None,
        command = None,
        environment = {},
        volumes = {},
        memory = '250m',
        wait = 30,
        **options
    ):
        if not self.client:
            return

        data = self.get_service(name, create = False)
        if data and self._service_container(data['id']):
            return data['id']

        self.print("{} {}".format(
            self.notice_color('Launching Zimagi service'),
            self.key_color(name)
        ))
        options = normalize_value(options)
        container_name = self._normalize_name(name)
        network = self._get_network("{}-{}".format(self.app_name, self.env.name))

        dns_map = {}
        for spec_name, spec in self.get_spec('services').items():
            dns_map[self._normalize_name(spec_name)] = spec_name

        volume_info = {}
        for local_path, remote_config in volumes.items():
            if local_path[0] != '/':
                local_path = self._normalize_name(local_path)
                self._get_volume(local_path)

            volume_info[local_path] = remote_config

        options.pop('requires', None)

        if options.get('runtime', '') == 'standard':
            options.pop('runtime')

        service = self._service_container(container_name)
        if service:
            service.remove(force = True)

        service = self.client.containers.run(image,
            entrypoint = entrypoint,
            command = command,
            name = container_name,
            hostname = name,
            links = dns_map,
            detach = True,
            mem_limit = memory,
            network = network.name,
            ports = ports,
            volumes = volume_info,
            environment = environment,
            **options
        )
        success, service = self._check_service(name, service)
        self._save_service(name, service.id, {
            'image': image,
            'volumes': volumes,
            'success': success
        })
        if not success:
            self._service_error(name, service)

        return service.id


    def stop_service(self, name, remove = False, remove_network = True, remove_image = False, remove_volumes = False):
        if not self.client:
            return

        data = self.get_service(name, restart = False, create = False)
        if data:
            operation = 'Destroying' if remove else 'Stopping'
            self.print("{} {}".format(
                self.notice_color("{} Zimagi service".format(operation)),
                self.key_color(name)
            ))
            container = self.client.containers.get(data['id'])
            container.stop()

            if remove:
                container.remove()
                try:
                    if remove_volumes:
                        for local_path, remote_config in data['volumes'].items():
                            if local_path[0] != '/':
                                self._get_volume(self._normalize_name(local_path)).remove(force = True)
                    if remove_image:
                        self.client.images.remove(container.image.name)
                    if remove_network:
                        network_name = "{}-{}".format(self.app_name, self.env.name)
                        self.client.networks.prune({ 'name': network_name })
                except Exception:
                    pass

                self._delete_service(name)
        else:
            service = self._service_container(self._normalize_name(name))
            if service:
                service.remove(force = True)


    def _service_error(self, name, service):
        error_message = "Service {} terminated with errors".format(name)
        log_message = ''

        try:
            log_message = "\n\n{}".format(service.logs().decode('utf-8').strip())
        except docker.errors.APIError as error:
            pass

        self.stop_service(name, True)
        raise ServiceError("{}{}".format(error_message, log_message))


    def display_service_logs(self, names, tail = 20, follow = False):
        if self.client:
            names = ensure_list(names, True)

            def display_logs(name):
                data = self.get_service(name, restart = False, create = False)
                if data:
                    container = self.client.containers.get(data['id'])

                    if follow:
                        initial_logs = True
                        while container.status == 'running':
                            lines = tail if initial_logs else 0
                            for message in container.logs(stream = follow, follow = follow, tail = lines):
                                self.print("[ {} ] {}".format(self.key_color(name), self.value_color(message.decode('utf-8').strip())))
                            initial_logs = False
                    else:
                        for message in container.logs(stream = False, follow = False, tail = tail).decode('utf-8').split("\n"):
                            self.print("[ {} ] {}".format(self.key_color(name), self.value_color(message.strip())))
                else:
                    self.print(self.warning_color("Service {} has not been created or is not running".format(name)))

            results = Parallel.list(names, display_logs)
            if results.aborted:
                raise ServiceError("\n".join([ str(error) for error in results.errors ]))


    def get_service_shell(self, name, shell = 'bash'):
        name = self._normalize_name(name)
        subprocess.call("docker exec --interactive --tty {} {}".format(name, shell), shell = True)
