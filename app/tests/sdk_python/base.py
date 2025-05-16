import os

from django.conf import settings
from django.test import TestCase
from utility.filesystem import load_yaml

import zimagi

from ..mixins.assertions import TestAssertions

zimagi.settings.COMMAND_RAISE_ERROR = True


class BaseTest(TestAssertions, TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        api_protocol = "http" if settings.COMMAND_HOST == "localhost" else "https"

        cls.command_api = zimagi.CommandClient(
            protocol=api_protocol,
            host=settings.COMMAND_HOST,
            port=settings.COMMAND_PORT,
            user=settings.API_USER,
            token=settings.API_USER_TOKEN,
            encryption_key=settings.ADMIN_API_KEY,
            message_callback=cls._message_callback,
        )
        cls.data_api = zimagi.DataClient(
            protocol=api_protocol,
            host=settings.DATA_HOST,
            port=settings.DATA_PORT,
            user=settings.API_USER,
            token=settings.API_USER_TOKEN,
            encryption_key=settings.ADMIN_API_KEY,
        )

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

    def _fixture_teardown(self):
        pass

    @classmethod
    def _message_callback(cls, message):
        message.display()

    @classmethod
    def _load_data(cls, data_type):
        return load_yaml(os.path.join(settings.BASE_TEST_DIR, "data", f"{data_type}.yml"))
