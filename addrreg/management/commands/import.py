import json

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
    },
    'district': {
        None: models.District,
        'UID': 'id',
        'state': 'state_id',
    },
    'postalcode': {
        None: models.PostalCode,
        'UID': 'id',
        'state': 'state_id',
        'postalarea': 'name',
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
    },
    'road': {
        None: models.Road,
        'UID': 'id',
        'state': 'state_id',
        'shortname20': 'shortname',
        'nameda': 'danish_name',
        'nameCPR': 'cpr_name',
        'locationID': 'location_id',
        'municipalityID': 'municipality_id',
    },
    'address': {
        None: models.Address,
        'UID': 'id',
        'State': 'state_id',
        'housenumber': 'house_number',
        'bnumberID': 'b_number_id',
        'roadID': 'road_id',
        'MunicipalityID': 'municipality_id',
    },
}

OVERRIDES = {
    99732: {
        'postal_code_id': None,
    }
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
}


def import_spreadsheet(fp, verbose=False, raise_on_error=False):
    wb = openpyxl.load_workbook(fp, read_only=True, data_only=True)

    for sheet in wb:
        try:
            mapping = SPREADSHEET_MAPPINGS[sheet.title]
        except KeyError:
            continue

        cls = mapping.pop(None)

        if verbose:
            print('importing {} {}'.format(
                sheet.max_row, cls._meta.verbose_name_plural
            ))

        rows = sheet.rows

        column_names = [
            mapping.get(col.value, col.value)
            for col in next(rows)
        ]

        for i, row in enumerate(rows):
            if verbose and not i % 50:
                total = sheet.max_row - 2
                print('{:3.0f}% - {} of {}{}'.format(
                    i / total * 100, i, total, ' ' * 5),
                    end='\r'
                )

            if row[0].value in DROP:
                continue

            try:
                kws = {
                    column_names[cellidx]:
                        (VALUE_MAPS[column_names[cellidx]].get(cell.value,
                                                               cell.value)
                         if column_names[cellidx] in VALUE_MAPS else cell.value)
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
                item = cls.objects.create(**kws)
                models.events.Event.create(item)
            except (db.Error, exceptions.ValidationError,
                    exceptions.ObjectDoesNotExist) as exc:
                msg = 'error processing {} {}: {}'.format(
                    sheet.title, kws['id'], json.dumps(kws, indent=2),
                )

                if raise_on_error:
                    raise base.CommandError(msg)
                else:
                    print(msg)

    if verbose:
        print('done!' + 20 * ' ')


class Command(base.BaseCommand):
    help = 'Import the given spreadsheet into the database'

    def add_arguments(self, parser):
        parser.add_argument('--failfast', action='store_true',
                            help='stop on first error')
        parser.add_argument('path', type=str, nargs='?',
                            default='fixtures/'
                                    'Adropslagdata_20170423_datatotal.xlsx',
                            help='the file to import')

    def handle(self, *args, **kwargs):
        with open(kwargs['path'], 'rb') as fp:
            import_spreadsheet(fp, kwargs['verbosity'] > 0, kwargs['failfast'])
