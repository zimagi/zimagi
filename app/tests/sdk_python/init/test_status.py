from django.test import tag
from tests.sdk_python.base import BaseTest


SUCCESS_MESSAGE = 'System check successful'


@tag('init', 'status')
class StatusTest(BaseTest):

    @tag('data_status')
    def test_data_status(self):
        status_info = self.data_api.get_status()
        self.assertEqual(status_info['message'], SUCCESS_MESSAGE)


    @tag('command_status')
    def test_command_status(self):
        status_info = self.command_api.get_status()
        self.assertEqual(status_info['message'], SUCCESS_MESSAGE)
