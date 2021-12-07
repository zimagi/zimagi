from django.conf import settings

from systems.commands.index import Command

import re


class Clean(Command('clean')):

    def exec(self):
        base_image = re.sub(r'\:.+$', '', settings.DEFAULT_RUNTIME_IMAGE)
        image_count = -1

        def clean_images():
            images = []

            for image in self.manager.list_images():
                if not image.tags or re.match(r"^{}\:[\d]+$".format(base_image), image.tags[0]):
                    images.append(image)

            def remove(image):
                try:
                    self.manager.delete_image(image.id)
                    self.success("Successfully removed image: {}".format(image.tags[0]))

                except Exception as e:
                    self.error("Failed to delete image {}: {}".format(image.id, e))

            self.run_list(images, remove)
            return images

        while True:
            # Run potentially multiple times to clean dependent images
            count = clean_images()
            if count == image_count:
                break
            else:
                image_count = count
