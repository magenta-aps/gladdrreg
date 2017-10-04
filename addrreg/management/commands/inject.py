from ...tests import test_selenium

from django import test
from django.core.management.commands import flush


class Command(flush.Command):
    help = 'Inject Selenium test fixture'

    @test.override_settings(TESTING=True)
    def handle(self, **kwargs):
        super().handle(**kwargs)

        test_selenium.SeleniumTests().inject()
