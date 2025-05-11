import os

from django.conf import settings
from django.test import TestCase
from systems.commands import action
from utility.filesystem import load_yaml

import zimagi

from ..mixins.assertions import TestAssertions

zimagi.settings.COMMAND_RAISE_ERROR = True


class BaseTest(TestAssertions, TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.command = action.primary("sdk_test_case")

        host, created = cls.command._host.store(
            settings.TEST_HOST_NAME, {"host": "command-api", "encryption_key": settings.ADMIN_API_KEY}
        )
        cls.command_api = host.command_api(message_callback=cls._message_callback)
        cls.data_api = host.data_api()
        cls.setup()

    @classmethod
    def setup(cls):
        # Override in subclass if needed
        pass

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.tear_down()

    @classmethod
    def tear_down(cls):
        # Override in subclass if needed
        pass

    @classmethod
    def _message_callback(cls, message):
        message.display()

    @classmethod
    def _load_data(cls, data_type):
        return load_yaml(os.path.join(settings.BASE_TEST_DIR, "data", f"{data_type}.yml"))
