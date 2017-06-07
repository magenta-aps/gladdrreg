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
        'sumiffiik_ID': 'sumiffiik',
    },
    'district': {
        None: models.District,
        'UID': 'id',
        'state': 'state_id',
        'sumiffiik_ID': 'sumiffiik',
    },
    'postalcode': {
        None: models.PostalCode,
        'UID': 'id',
        'state': 'state_id',
        'postalarea': 'name',
        'sumiffiik_ID': 'sumiffiik',
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
        'sumiffiik_ID': 'sumiffiik',
    },
    'bnumber': {
        None: models.BNumber,
        'UID': 'id',
        'StateID': 'state_id',
        'Code': 'code',
        'bcallName': 'nickname',
        'bunitName': 'name',
        'LocalityID': 'location_id',
        'MunicipalityID': 'municipality_id',
        'Note': 'note',
        'sumiffiik_ID': 'sumiffiik',
    },
    'road': {
        None: models.Road,
        'UID': 'id',
        'state': 'state_id',
        'shortname20': 'shortname',
        'nameCPR': 'cpr_name',
        'locationID': 'location_id',
        'municipalityID': 'municipality_id',
        'sumiffiik_id': 'sumiffiik',
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
        'sumiffiik_ID': 'sumiffiik',
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
        'https://data.gl/najugaq/{}/v1'.format(title)
        for title in SPREADSHEET_MAPPINGS
    },
}


def import_spreadsheet(fp, verbose=False, raise_on_error=False):
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

            if db.connection.vendor == 'sqlite':
                pool_size = 1
            else:
                pool_size = 3

            # executing two saves concurrently ensures that we'll
            # typically be preparing the next while waiting for the
            # current one to save in the database
            with concurrent.futures.ThreadPoolExecutor(pool_size) as e:
                for f in e.map(save, rows):
                    bar.next()
    finally:
        bar.finish()


class Command(base.BaseCommand):
    help = 'Import the given spreadsheet into the database'

    def add_arguments(self, parser):
        parser.add_argument('--failfast', action='store_true',
                            help='stop on first error')
        parser.add_argument('path', type=str, nargs='?',
                            default='fixtures/'
                                    'Adropslagdata_20170510_datatotal.xlsx',
                            help='the file to import')

    def handle(self, *args, **kwargs):
        with open(kwargs['path'], 'rb') as fp:
            import_spreadsheet(fp, kwargs['verbosity'] > 0, kwargs['failfast'])
