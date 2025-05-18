from django.test.runner import DiscoverRunner


class TestRunner(DiscoverRunner):

    def run_tests(self, test_labels, extra_tests=None, **kwargs):
        self.setup_test_environment()
        suite = self.build_suite(test_labels)
        run_failed = False
        try:
            result = self.run_suite(suite)
        except Exception:
            run_failed = True
            raise
        finally:
            try:
                self.teardown_test_environment()
            except Exception:
                # Silence teardown exceptions if an exception was raised during
                # runs to avoid shadowing it.
                if not run_failed:
                    raise
        self.time_keeper.print_results()
        return self.suite_result(suite, result)
