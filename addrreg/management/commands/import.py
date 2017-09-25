import concurrent.futures
import itertools
import json
import traceback

import progress.bar
import openpyxl

from django import db
from django.core import exceptions
from django.core.management import base

from ... import models

SPREADSHEET_MAPPINGS = {
    'state': {
        None: models.State,
        'UID': 'id',
        'statestate': 'state_id',
        'state': 'name',
    },
    'municipality': {
        None: models.Municipality,
        'UID': 'id',
        'state': 'state_id',
        'sumiiffik_ID': 'sumiffiik',
        'sumiiffik_domain': 'sumiffiik_domain',
    },
    'district': {
        None: models.District,
        'UID': 'id',
        'state': 'state_id',
        'sumiiffik_ID': 'sumiffiik',
        'sumiiffik_domain': 'sumiffiik_domain',
    },
    'postalcode': {
        None: models.PostalCode,
        'UID': 'id',
        'state': 'state_id',
        'postalarea': 'name',
        'sumiiffik_ID': 'sumiffiik',
        'sumiiffik_domain': 'sumiffiik_domain',
    },
    'locality': {
        None: models.Locality,
        'UID': 'id',
        'state': 'state_id',
        'municipalityID': 'municipality_id',
        'postalcodeID': 'postal_code_id',
        'districtID': 'district_id',
        'typecodeID': 'type',
        'statecodeID': 'locality_state',
        'sumiiffik_ID': 'sumiffiik',
        'sumiiffik_domain': 'sumiffiik_domain',
    },
    'bnumber': {
        None: models.BNumber,
        'UID': 'id',
        'StateID': 'state_id',
        'Code': 'code',
        'bcallName': 'b_callname',
        'bunitName': 'b_type',
        'LocalityID': 'location_id',
        'MunicipalityID': 'municipality_id',
        'Note': 'note',
        'sumiiffik_ID': 'sumiffiik',
        'sumiiffik_domain': 'sumiffiik_domain',
    },
    'road': {
        None: models.Road,
        'UID': 'id',
        'state': 'state_id',
        'shortname20': 'shortname',
        'nameCPR': 'cpr_name',
        'locationID': 'location_id',
        'municipalityID': 'municipality_id',
        'sumiiffik_id': 'sumiffiik',
        'sumiiffik_domain': 'sumiffiik_domain',
        'name_alt': 'alternate_name',
    },
    'address': {
        None: models.Address,
        'UID': 'id',
        'State': 'state_id',
        'Houseno': 'house_number',
        'Door': 'room',
        'bnumberID': 'b_number_id',
        'roadID': 'road_id',
        'MunicipalityID': 'municipality_id',
        'sumiiffik_ID': 'sumiffiik',
        'sumiiffik_domain': 'sumiffiik_domain',
    },
}

OVERRIDES = {
}

DROP = {
    # bad localities
    99701,
    99810,
    99811,
    99812,
    99813,
    99814,
    99815,
    # bad roads
    98105,
    98106,
    98107,
    98108,
    98109,
    98110,
    97000,
}

VALUE_MAPS = {
    'active': {
        None: True,
        True: True,
        False: False,
    },
    'type': {
        None: models.LocalityType.UNKNOWN,
        99981: models.LocalityType.UNKNOWN,
        99982: models.LocalityType.TOWN,
        99983: models.LocalityType.SETTLEMENT,
        99984: models.LocalityType.MINE,
        99985: models.LocalityType.STATION,
        99986: models.LocalityType.AIRPORT,
        99987: models.LocalityType.FARM,
        99988: models.LocalityType.DEVELOPMENT,
    },
    'locality_state': {
        99971: models.LocalityState.PROJECTED,
        99972: models.LocalityState.ACTIVE,
        99973: models.LocalityState.ABANDONED,
    },
    'state_id': dict([(None, 99991)] + [(i, 99990 + i) for i in range(7)]),
    'sumiffiik_domain': {
        'https://data.gl/naujat/{}/v1'.format(title):
        'https://data.gl/najugaq/{}'.format(title)
        for title in SPREADSHEET_MAPPINGS
    },
}


def import_spreadsheet(fp, verbose=False, raise_on_error=False,
                       interactive=True, parallel=1):
    object_count = sum(
        v[None].objects.count()
        for v in SPREADSHEET_MAPPINGS.values()
    )
    registration_count = sum(
        v[None].Registrations.objects.count()
        for v in SPREADSHEET_MAPPINGS.values()
        if getattr(v[None], 'Registrations', None)
    )

    message = """
You have requested an import into the database even though it has {}
objects and {} registrations. This may overwrite or conflict with
any pre-existing entries.
Are you sure you want to do this?

   Type 'yes' to continue, or 'no' to cancel:
""".strip('\n').format(object_count, registration_count)

    if (interactive and object_count + registration_count and
            input(message + ' ') != 'yes'):
        raise CommandError("Import cancelled.")

    wb = openpyxl.load_workbook(fp, read_only=True, data_only=True)

    total = sum(sheet.max_row - 1 for sheet in wb
                if sheet.title in SPREADSHEET_MAPPINGS)
    bar = progress.bar.Bar(max=total,
                           suffix='%(index).0f of %(max).0f - '
                                  '%(elapsed_td)s / %(eta_td)s')

    try:
        for sheet in wb:
            try:
                mapping = SPREADSHEET_MAPPINGS[sheet.title]
            except KeyError:
                continue

            cls = mapping.pop(None)

            rows = sheet.rows

            column_names = [
                mapping.get(col.value, col.value and col.value.lower())
                for col in next(rows)
            ]

            def save(row):
                if row[0].value in DROP:
                    return

                try:
                    kws = {
                        column_names[cellidx]:
                            (VALUE_MAPS[column_names[cellidx]].get(cell.value,
                                                                   cell.value)
                             if column_names[cellidx] in VALUE_MAPS
                             else cell.value)
                        for cellidx, cell in enumerate(row)
                        if column_names[cellidx]
                    }
                except KeyError:
                    msg = 'error mapping {} {}: {}'.format(
                        sheet.title, kws['id'], json.dumps({
                            column_names[cellidx]: cell.value
                            for cellidx, cell in enumerate(row)
                            if column_names[cellidx]
                        }, indent=2)
                    )

                    if raise_on_error:
                        raise base.CommandError(msg)
                    else:
                        print(msg)

                try:
                    kws.update(OVERRIDES[kws['id']])
                except KeyError:
                    pass

                try:
                    cls.objects.create(**kws)
                except (db.Error, exceptions.ValidationError,
                        exceptions.ObjectDoesNotExist) as exc:
                    msg = 'error processing {} {}: {}'.format(
                        sheet.title, kws['id'], json.dumps(kws, indent=2),
                    )

                    if raise_on_error:
                        raise base.CommandError(msg)
                    elif verbose:
                        print(msg)
                        traceback.print_exc()
                    else:
                        print(msg)

            if sheet.title == 'state':
                # HACK: work around the fact that the first state refers
                # to the second state, by importing them in reverse order
                for row in reversed(list(itertools.islice(rows, 2))):
                    save(row)
                    bar.next()

            # executing two saves concurrently ensures that we'll
            # typically be preparing the next while waiting for the
            # current one to save in the database
            with concurrent.futures.ThreadPoolExecutor(parallel) as e:
                for f in e.map(save, rows):
                    bar.next()
    finally:
        bar.finish()


class Command(base.BaseCommand):
    help = 'Import the given spreadsheet into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--noinput', '--no-input',
            action='store_false', dest='interactive', default=True,
            help="Do NOT prompt the user for input of any kind.",
        )
        parser.add_argument('--failfast', action='store_true',
                            help='stop on first error')
        parser.add_argument(
            '--parallel', type=int,
            default=1 if db.connection.vendor == 'sqlite' else 4,
            help=u"amount of requests to perform in parallel"
        )
        parser.add_argument('path', type=str, nargs='?',
                            default='fixtures/'
                                    'Adropslagdata_20170510_datatotal.xlsx',
                            help='the file to import')

    def handle(self, *args, **kwargs):
        with open(kwargs['path'], 'rb') as fp:
            import_spreadsheet(
                fp=fp,
                verbose=kwargs['verbosity'] > 0,
                raise_on_error=kwargs['failfast'],
                interactive=kwargs['interactive'],
                parallel=kwargs['parallel'],
            )
