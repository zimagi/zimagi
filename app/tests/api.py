from .base import BaseTest


class Test(BaseTest):

    def exec(self):
        host = self.get_host()

        def run_tests(module_name):
            self.run_tests(module_name, host)

        if host:
            self.command.info("Running API tests...")
            self.command.run_list(self.get_test_libs('client'), run_tests)
