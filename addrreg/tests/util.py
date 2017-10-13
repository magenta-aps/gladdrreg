import logging
import sys

from django.test import override_settings, runner

DUMMY_DOMAIN = 'http://localhost'


class TestRunner(runner.DiscoverRunner):
    '''
    A Django test runner that enables output buffering.
    '''

    def get_test_runner_kwargs(self):
        kwargs = super().get_test_runner_kwargs()

        kwargs.update(
            buffer=True,
        )

        return kwargs

    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        self.log_stream_handler = logging.StreamHandler(sys.stdout)
        self.log_stream_handler.setLevel(logging.DEBUG)

        logging.getLogger('django').addHandler(self.log_stream_handler)

    def teardown_test_environment(self, **kwargs):
        super().teardown_test_environment(**kwargs)
        logging.getLogger('django').removeHandler(self.log_stream_handler)

    @override_settings(TESTING=True)
    def run_tests(self, *args, **kwargs):
        return super().run_tests(*args, **kwargs)
