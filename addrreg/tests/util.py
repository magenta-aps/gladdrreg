import logging
import sys

from django.test import runner

DUMMY_DOMAIN = 'http://localhost'


class TestRunner(runner.DiscoverRunner):
    '''
    A Django test runner that enables output buffering.
    '''

    def run_suite(self, suite, **kwargs):
        resultclass = self.get_resultclass()

        # TODO: we can simplify this code when we switch to Django 1.11
        return self.test_runner(
            verbosity=self.verbosity,
            failfast=self.failfast,
            resultclass=resultclass,
            buffer=True,
        ).run(suite)

    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        self.log_stream_handler = logging.StreamHandler(sys.stdout)
        self.log_stream_handler.setLevel(logging.DEBUG)

        logging.getLogger('django').addHandler(self.log_stream_handler)

    def teardown_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        logging.getLogger('django').removeHandler(self.log_stream_handler)
