import os

from django.conf import settings
from django.test.runner import get_max_test_processes
from django.test.utils import TimeKeeper

import zimagi

from .base import BaseTest
from .sdk_python.runner import TestRunner

zimagi.settings.THREAD_COUNT = 2


class Test(BaseTest):
    def exec(self):
        processes = settings.TEST_PROCESS_COUNT if settings.TEST_PROCESS_COUNT else get_max_test_processes()

        self.command.data("Max processes available", processes)

        time_keeper = TimeKeeper()
        runner_options = {
            "interactive": False,
            "debug_sql": settings.DEBUG,
            "timing": True,
            "keepdb": True,
            "tags": self.tags,
            "exclude_tags": self.exclude_tags,
            "parallel": processes,
        }
        zimagi.settings.PARALLEL = True

        for test_dir in ("init", "data"):
            with time_keeper.timed(f"Total run: {test_dir}"):
                test_runner = TestRunner(**runner_options)
                failures = test_runner.run_tests([os.path.join(settings.BASE_TEST_DIR, "sdk_python", test_dir)])
            time_keeper.print_results()

            if failures:
                self.command.error(f"Test suite api {test_dir} failed")
