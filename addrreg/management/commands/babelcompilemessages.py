import os
import sys

from django.conf import settings
from django.core.management import base

from babel.messages import frontend


class Command(base.BaseCommand):
    help = 'Compile our translations using Babel'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **kwargs):
        frontend.CommandLineInterface().run([
            sys.argv[0], 'compile',
            '--statistics',
            '-d', os.path.join(settings.BASE_DIR, 'i18n'),
            '-D', 'django',
        ])
