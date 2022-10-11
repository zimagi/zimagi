from django.conf import settings
from django.test.runner import get_max_test_processes
from django.test.utils import TimeKeeper

from .base import BaseTest
from .sdk_python.runner import TestRunner

import os


class Test(BaseTest):

    def exec(self):
        time_keeper = TimeKeeper()
        runner_options = {
            'interactive': False,
            'debug_sql': settings.DEBUG,
            'timing': True,
            'keepdb': True
        }
        if not self.command.no_parallel:
            runner_options['parallel'] = get_max_test_processes()

        for test_dir in ('init', 'data'):
            with time_keeper.timed("Total run: {}".format(test_dir)):
                test_runner = TestRunner(**runner_options)
                failures = test_runner.run_tests([
                    os.path.join(settings.BASE_TEST_DIR, 'sdk_python', test_dir)
                ])
            time_keeper.print_results()

            if failures:
                self.command.error("Test suite api {} failed".format(test_dir))
