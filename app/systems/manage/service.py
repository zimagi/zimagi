from django.core.management.base import CommandError

from utility.shell import Shell

import os
import docker
import pathlib
import json
import re
import time
import datetime
import logging


logger = logging.getLogger(__name__)


class ManagerServiceMixin(object):

    def __init__(self):
        self.client = docker.from_env()
        super().__init__()


    @property
    def container_id(self):
        return Shell.capture(('cat', '/proc/1/cpuset')).split('/')[-1]

    def service_container(self, id):
        try:
            return self.client.containers.get(id)
        except docker.errors.NotFound:
            return None


    def service_file(self, name):
        directory = os.path.join(self.data_dir, 'run')
        pathlib.Path(directory).mkdir(mode = 0o700, parents = True, exist_ok = True)
        return os.path.join(directory, "{}.data".format(name))

    def save_service(self, command, name, id, data = None):
        if not data:
            data = {}

        data['id'] = id
        with open(self.service_file(name), 'w') as file:
            file.write(json.dumps(data))

    def get_service(self, command, name, wait = 10, create = True):
        service_file = self.service_file(name)
        if os.path.isfile(service_file):
            with open(self.service_file(name), 'r') as file:
                data = json.loads(file.read())
                service = self.service_container(data['id'])
                if service:
                    if service.status != 'running':
                        if create:
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


    def generate_image_name(self, base_image):
        repository = base_image.split(':')[0]
        time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        return "{}:{}".format(repository, time)

    def create_image(self, id, image_name):
        container = self.service_container(id)
        if container:
            container.commit(image_name)

    def delete_image(self, image_name):
        image = self.client.images.get(image_name)
        self.client.images.remove(image.id)


    def create_volume(self, name):
        return docker.from_env().volumes.create(name)


    def check_service(self, command, name, service, wait = 30):
        success = True

        for index in range(wait):
            service = self.client.containers.get(service.id)
            if service.status == 'restarting':
                success = False
                break
            time.sleep(1)

        return (success, service)


    def start_service(self, command, name, image, ports,
        docker_entrypoint = None,
        docker_command = None,
        network_mode = 'bridge',
        environment = {},
        volumes = {},
        memory = '250m',
        wait = 30
    ):
        if command:
            command.info("Starting service {} ({}) with {} > {}".format(name, image, docker_entrypoint, docker_command))

        data = self.get_service(command, name, wait = wait)
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
            network_mode = network_mode,
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

    def stop_service(self, command, name, remove = False):
        if command:
            command.info("Stopping service {}".format(name))

        data = self.get_service(command, name, create = False)
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
