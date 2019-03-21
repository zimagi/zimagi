from django.conf import settings

from settings.config import Config
from utility import shell

import os
import time
import datetime
import docker


class MetaDocker(type):

    @property
    def container_id(self):
        return shell.Shell.capture(('cat', '/proc/1/cpuset')).split('/')[-1]


    def generate_image(self, base_image):
        repository = base_image.split(':')[0]
        time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        return "{}:{}".format(repository, time)

    def create_image(self, id, image_name):
        client = docker.from_env()
        container = client.containers.get(id)
        container.commit(image_name)


    def start_postgres(self, command,
        memory = '500m'
    ):
        self.start_service(
            command,
            'cenv-postgres',
            "postgres:11",
            { 5432: None },
            environment = self.parse_environment('pg.credentials'),
            volumes = {
                'cenv-postgres': {
                    'bind': '/var/lib/postgresql',
                    'mode': 'rw'
                }
            },
            memory = memory,
            wait = 20
        )

    def stop_postgres(self, command):
        self.stop_service(command, 'cenv-postgres')


    def parse_environment(self, env_name, variables = {}):
        env_file = os.path.join(settings.DATA_DIR, "{}.env".format(env_name))
        return Config.load(env_file)


    def create_volume(self, name):
        return docker.from_env().volumes.create(name)


    def start_service(self, command, name, image, ports,
        docker_entrypoint = None,
        docker_command = None,
        environment = {},
        volumes = {},
        memory = '250m',
        wait = 30
    ):
        client = docker.from_env()
        success = True
        service = settings.MANAGER.get_service(name)
        if service:
            try:
                client.containers.get(service['id'])
                command.notice("Service {} is already running".format(name))
                return

            except docker.errors.NotFound:
                pass

        for local_path, remote_config in volumes.items():
            if local_path[0] != '/':
                self.create_volume(local_path)

        container = client.containers.run(image,
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
        for index in range(wait):
            service = client.containers.get(container.id)
            if service.status == 'restarting':
                success = False
                break
            time.sleep(1)

        service = client.containers.get(container.id)
        settings.MANAGER.save_service(name, container.id, {
            'image': image,
            'ports': service.attrs["NetworkSettings"]["Ports"],
            'environment': environment,
            'volumes': volumes,
            'success': success
        })
        if not success:
            command.info(command.notice_color(container.logs().decode("utf-8").strip()))
            self.stop_service(command, name)
            command.error("Service {} terminated with errors".format(name))

    def stop_service(self, command, name):
        service = settings.MANAGER.get_service(name)
        if service:
            container = docker.from_env().containers.get(
                service['id']
            )
            container.stop()
            container.remove()
            settings.MANAGER.delete_service(name)
        else:
            command.notice("Service {} is not running".format(name))


class Docker(object, metaclass = MetaDocker):
    pass