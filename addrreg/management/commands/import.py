from django.core.management.base import BaseCommand, CommandError
from ... import utils

class Command(BaseCommand):
    help = 'Import the given spreadsheet into the database'

    def add_arguments(self, parser):
        parser.add_argument('path', type=str)

    def handle(self, *args, **kwargs):
        with open(kwargs['path'], 'rb') as fp:
            utils.import_spreadsheet(fp)
