from django.core.management import base
from django.utils import translation
from ... import utils

class Command(base.BaseCommand):
    help = 'Import the given spreadsheet into the database'

    def add_arguments(self, parser):
        parser.add_argument('path', type=str)

    def handle(self, *args, **kwargs):
        with translation.override('da'), open(kwargs['path'], 'rb') as fp:
                utils.import_spreadsheet(fp, verbose=kwargs['verbosity'] > 0)
