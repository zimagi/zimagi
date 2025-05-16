import os

from django.conf import settings
from django.test.runner import get_max_test_processes
from django.test.utils import TimeKeeper
from tests.sdk_python.runner import TestRunner

from .action import ActionCommand


class TestCommand(ActionCommand):

    def exec(self):
        test_types = self.options.get("test_types", [])

        if not test_types:
            self._exec_python_sdk()
            super().exec()

        elif "python_sdk" in test_types:
            self.options["test_types"] = [type for type in test_types if type != "python_sdk"]
            self._exec_python_sdk()

        if self.options.get("test_types", None):
            super().exec()

    def _exec_python_sdk(self):
        processes = settings.TEST_PROCESS_COUNT if settings.TEST_PROCESS_COUNT else get_max_test_processes()

        self.print("Running python_sdk tests...")
        self.print(f"Max processes available: {processes}")

        time_keeper = TimeKeeper()
        runner_options = {
            "interactive": False,
            "debug_sql": settings.DEBUG,
            "timing": True,
            "keepdb": False,
            "tags": self.options.get("test_tags", []),
            "exclude_tags": self.options.get("test_exclude_tags", []),
            "parallel": processes,
        }
        for test_dir in ("init", "data"):
            with time_keeper.timed(f"Total run: {test_dir}"):
                test_runner = TestRunner(**runner_options)
                failures = test_runner.run_tests([os.path.join(settings.BASE_TEST_DIR, "sdk_python", test_dir)])
            time_keeper.print_results()

            if failures:
                raise Exception(f"Test suite api {test_dir} failed")
