from tests.sdk_python.base import BaseTest


SUCCESS_MESSAGE = 'System check successful'


class StatusTest(BaseTest):

    def test_data_status(self):
        status_info = self.data_api.get_status()
        self.assertEqual(status_info['message'], SUCCESS_MESSAGE)

    def test_command_status(self):
        status_info = self.command_api.get_status()
        self.assertEqual(status_info['message'], SUCCESS_MESSAGE)
