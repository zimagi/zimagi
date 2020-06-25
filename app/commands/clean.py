from docker.errors import APIError
from django.conf import settings

from systems.commands.index import Command

import re


class Clean(Command('clean')):

    def exec(self):
        base_image = re.sub(r'\:.+$', '', settings.DEFAULT_RUNTIME_IMAGE)

        def clean_images():
            images = []

            for image in self.manager.client.images.list():
                if re.match(r"^{}\:[\d]+$".format(base_image), image.tags[0]):
                    images.append(image)

            def remove(image):
                try:
                    self.manager.client.images.remove(image.id)
                    self.success("Successfully removed image: {}".format(image.tags[0]))

                except APIError as e:
                    if e.response.status_code != 409:
                        self.error("Failed to delete image {}: {}".format(image.id, e))

            self.run_list(images, remove)
            return images

        while True:
            # Run potentially multiple times to clean dependent images
            if len(clean_images()) <= 1:
                break
