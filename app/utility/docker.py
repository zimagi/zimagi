from utility import shell

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


class Docker(object, metaclass = MetaDocker):
    pass