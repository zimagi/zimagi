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
        try:
            self.client = docker.from_env()
        except Exception:
            self.client = None

        super().__init__()


    @property
    def container_id(self):
        return Shell.capture(('cat', '/proc/1/cpuset')).split('/')[-1]

    def service_container(self, id):
        if self.client:
            try:
                return self.client.containers.get(id)
            except docker.errors.NotFound:
                pass

        return None


    def generate_image_name(self, base_image):
        repository = base_image.split(':')[0]
        time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        return "{}:{}".format(repository, time)


    def list_images(self):
        if self.client:
            return self.client.images.list()
        return []

    def create_image(self, id, image_name):
        container = self.service_container(id)
        if container:
            container.commit(image_name)

    def delete_image(self, image_name, force = True, noprune = False):
        if self.client:
            image = self.client.images.get(image_name)
            self.client.images.remove(image.id, force = force, noprune = noprune)
