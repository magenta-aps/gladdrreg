# -*- mode: python; coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals, print_function

import datetime
import os
import pycodestyle
import pytz
import six

from django import test

# Create your tests here.
from . import models


class CodeStyleTest(test.TestCase):
    skip_dirs = (
        'migrations',
    )

    @property
    def rootdir(self):
        return os.path.dirname(os.path.dirname(__file__))

    @property
    def source_files(self):
        """Generator that yields Python sources to test"""

        for dirpath, dirs, fns in os.walk(self.rootdir):
            dirs[:] = [dn for dn in dirs if dn not in self.skip_dirs]

            for fn in fns:
                if fn.endswith('.py'):
                    yield os.path.join(dirpath, fn)

    def test_pep8(self):
        pep8style = pycodestyle.StyleGuide(quiet=True)
        # pep8style.init_report(pep8.StandardReport)
        # pep8style.input_dir(self.rootdir)
        for fn in self.source_files:
            r = pep8style.check_files([fn])

            self.assertEqual(r.messages, {},
                             "Found code style errors (and warnings) in %s."
                             % fn)


class CreationTests(test.TestCase):

    def setUp(self):
        now = datetime.datetime.now(pytz.UTC)

        mun = models.Municipality.objects.create(
            name='Aarhus',
            code=20,
            # valid_datetime_start=now,
        )

        road = models.Road.objects.create(
            code=1337,
            name='Hans Hartvig Seedorffs Stræde',
            shortname='H H Seedorffs Stræde',
            dkName='Hans Hartvig Seedorffs Stræde',
            # this translation is quite likely horribly wrong
            glName='Hans Hartvig Seedorffs aqqusineq amitsoq',
            cprName='Hans Hartvig Seedorff\'s Street',
            # valid_datetime_start=now,
        )

        pc = models.PostalCode.objects.create(
            code=8000,
            name='Aarhus C',
            # valid_datetime_start=now,
        )

        b = models.BNumber.objects.create(
            number=42,
            name='The Block',
            block='BS221B',
            municipality=mun,
            # valid_datetime_start=now,
        )

        self.addr = models.Address.objects.create(
            houseNumber='42Z',
            floor='Mezzanine',
            door='Up',
            locality=None,
            bNumber=b,
            road=road,
            postalCode=pc,
            # valid_datetime_start=now,
        )

    def test_addr(self):
        self.assertEquals(self.addr.bNumber.municipality.name, 'Aarhus')
        self.assertEquals(self.addr.bNumber.municipality.name, 'Aarhus')
        self.assertEquals(six.text_type(self.addr),
                          '42Z Hans Hartvig Seedorffs Stræde')


class ImportTests(test.TestCase):

    def setUp(self):
        self.fixture_path = os.path.join(
            os.path.dirname(__file__),
            '..', 'fixtures', 'adresse-register.xlsx'
        )
        self.fp = open(self.fixture_path, 'rb')

    def tearDown(self):
        self.fp.close()

    def test_read(self):
        x = list(models.read_spreadsheet(self.fp))

        self.assertEquals(
            sorted(x[0]),
            [
                'BEMÆRKNING',
                'BLOKKE',
                'BNR',
                'BNR-HUSNR',
                'BNR_TAL',
                'ENS_LOKATION',
                'ETAGE',
                'HUSNR',
                'KOMMUNEKODE',
                'KOMNAVN',
                'LOKALITETSNAVN',
                'LOKALITETSNR',
                'LOKALITETSSTATUS',
                'LOKALITETS_STATUS_NAVN',
                'LOKALITETS_TYPE',
                'LOKALITETS_TYPE_NAVN',
                'Nyk',
                'POSTDISTRIKT',
                'POSTNR',
                'Renset husnummer',
                'SIDE',
                'TYPE',
                'VEJKODE',
                'VEJNAVN',
            ],
        )

        self.assertEquals(len(x), 22913)

    def test_import_municipalities(self):
        for val in models.read_spreadsheet(self.fp):
            obj = models.Municipality.from_dict(val)
            self.assertEquals(obj.name, val['KOMNAVN'].rstrip())

    def test_import_locality(self):
        for val in models.read_spreadsheet(self.fp):
            obj = models.Locality.from_dict(val)

            if not obj:
                continue

            self.assertEquals(obj.name, val['LOKALITETSNAVN'].rstrip())
            self.assertEquals(obj.type, val['LOKALITETS_TYPE_NAVN'].rstrip())

    def test_import_postal_code(self):
        for val in models.read_spreadsheet(self.fp):
            obj = models.PostalCode.from_dict(val)
            self.assertEquals(obj.code, val['POSTNR'].rstrip())
            self.assertEquals(obj.name, val['POSTDISTRIKT'].rstrip())

    def test_import_b_number(self):
        for val in models.read_spreadsheet(self.fp):
            obj = models.BNumber.from_dict(val)
            self.assertEquals(obj.municipality.name, val['KOMNAVN'].rstrip())

    def test_import(self):
        models.import_spreadsheet(self.fp)
        self.assertEquals(len(models.Address.objects.all()), 22913)
