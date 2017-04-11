# -*- mode: python; coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals, print_function

import datetime
import unittest

import freezegun
import os
import pycodestyle
import pytz
from django import db, test
from django.core import exceptions
from django.utils import six

# Create your tests here.
from . import models


class CodeStyleTest(test.SimpleTestCase):
    @property
    def rootdir(self):
        return os.path.dirname(os.path.dirname(__file__))

    @property
    def source_files(self):
        """Generator that yields Python sources to test"""

        for dirpath, dirs, fns in os.walk(self.rootdir):
            dirs[:] = [
                dn for dn in dirs
                if dn == 'migrations' or dn.startswith('pyenv-')
            ]

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


class CreationTests(test.TransactionTestCase):
    reset_sequences = True

    def test_creation(self):
        mun = models.Municipality.objects.create(
            name='Aarhus',
            code=20,
        )

        road = models.Road(
            code=1337,
            name='Hans Hartvig Seedorffs Stræde',
            shortname='H H Seedorffs Stræde',
            dkName='Hans Hartvig Seedorffs Stræde',
            # this translation is quite likely horribly wrong
            glName='Hans Hartvig Seedorffs aqqusineq amitsoq',
            cprName='Hans Hartvig Seedorff\'s Street',
        )
        road.save()

        pc = models.PostalCode(
            code=8000,
            name='Aarhus C',
        )
        pc.save()

        b = models.BNumber(
            number='42',
            name='The Block',
            block='BS221B',
            municipality=mun,
        )
        b.save()

        self.addr = models.Address(
            houseNumber='42Z',
            floor='Mezzanine',
            door='Up',
            locality=None,
            bNumber=b,
            road=road,
            postalCode=pc,
        )
        self.addr.save()

        self.assertEquals(self.addr.bNumber.municipality.name, 'Aarhus')
        self.assertEquals(self.addr.bNumber.municipality.name, 'Aarhus')
        self.assertEquals(six.text_type(self.addr),
                          '42Z Hans Hartvig Seedorffs Stræde')

    def test_create_duplicate_municipality_fails(self):
        """Test that creating two municipalities with the same code fails."""
        models.Municipality.objects.create(
            name='Aarhus',
            code=20,
        )

        self.assertRaises(
            db.IntegrityError,
            models.Municipality.objects.create,
            name='Aarhus',
            code=20,
        )


class TemporalTests(test.TransactionTestCase):
    reset_sequences = True

    @staticmethod
    def _getregistrations():
        regs = models.Municipality.Registrations.objects.all()
        return sorted(regs.values('id', 'object', 'objectID',
                                  'registration_from', 'registration_to'),
                      key=lambda d: d.pop('id'))

    def test_create_and_delete(self):
        with freezegun.freeze_time('2001-01-01'):
            mun = models.Municipality.objects.create(
                name='Aarhus',
                code=20,
            )
        munid = mun.objectID
        self.assertEquals(mun.id, 1)

        self.assertEquals(
            self._getregistrations(),
            [
                {
                    'object': mun.id,
                    'objectID': munid,
                    'registration_from': datetime.datetime(2001, 1, 1, 0, 0,
                                                           tzinfo=pytz.UTC),
                    'registration_to': None,
                },
            ]
        )

        with freezegun.freeze_time('2001-01-02'):
            mun.note = 'Dette er en note.'
            mun.save()

        self.assertEquals(
            self._getregistrations(),
            [
                {
                    'object': mun.id,
                    'objectID': munid,
                    'registration_from': datetime.datetime(2001, 1, 1, 0, 0,
                                                           tzinfo=pytz.UTC),
                    'registration_to': datetime.datetime(2001, 1, 2, 0, 0,
                                                         tzinfo=pytz.UTC),
                },
                {
                    'object': mun.id,
                    'objectID': munid,
                    'registration_from': datetime.datetime(2001, 1, 2, 0, 0,
                                                           tzinfo=pytz.UTC),
                    'registration_to': None,
                },
            ]
        )

        with freezegun.freeze_time('2001-01-03'):
            mun.delete()

        self.assertEquals(
            self._getregistrations(),
            [
                {
                    'object': None,
                    'objectID': munid,
                    'registration_from': datetime.datetime(2001, 1, 1, 0, 0,
                                                           tzinfo=pytz.UTC),
                    'registration_to': datetime.datetime(2001, 1, 2, 0, 0,
                                                         tzinfo=pytz.UTC),
                },
                {
                    'object': None,
                    'objectID': munid,
                    'registration_from': datetime.datetime(2001, 1, 2, 0, 0,
                                                           tzinfo=pytz.UTC),
                    'registration_to': datetime.datetime(2001, 1, 3, 0, 0,
                                                         tzinfo=pytz.UTC),
                },
            ]
        )

        self.assertEquals(models.Municipality.Registrations.objects.count(), 2)
        self.assertEquals(models.Municipality.objects.count(), 0)

    def test_fail_delete(self):
        class MyException(Exception):
            pass

        def fail(self):
            raise MyException

        with freezegun.freeze_time('2001-01-01'):
            mun = models.Municipality.objects.create(
                name='Aarhus',
                code=20,
            )

        models.Municipality._maybe_intercept = fail

        try:
            self.assertRaises(MyException, mun.delete)
        finally:
            del models.Municipality._maybe_intercept

        self.assertEquals(self._getregistrations(), [{
            'object': mun.id,
            'objectID': mun.objectID,
            'registration_from':
                datetime.datetime(2001, 1, 1, 0, 0, tzinfo=pytz.UTC),
            'registration_to': None,
        }])

    def test_fail_create(self):
        class MyException(Exception):
            pass

        def fail(*args, **kwargs):
            raise MyException

        models.Municipality._maybe_intercept = fail

        try:
            self.assertRaises(MyException, models.Municipality.objects.create,
                              name='Aarhus', code=20)
        finally:
            del models.Municipality._maybe_intercept

        self.assertFalse(models.Municipality.objects.count(),
                         "failing transactions shouldn't create anything")
        self.assertFalse(models.Municipality.Registrations.objects.count(),
                         "failing transactions shouldn't create any "
                         "registrations")

    def test_evil_time(self):
        with freezegun.freeze_time('2001-01-02'):
            mun = models.Municipality.objects.create(
                name='Aarhus',
                code=20,
            )

        with freezegun.freeze_time('2001-01-01'):
            mun.note = 'flaf'
            self.assertRaises(exceptions.ValidationError, mun.save)

        with freezegun.freeze_time('2001-01-03'):
            mun.note = 'flaf'
            mun.save()

    def test_recreate(self):
        """
        Test that recreating an item?
        """
        with freezegun.freeze_time('2001-01-01'):
            mun = models.Municipality.objects.create(
                name='Aarhus',
                code=20,
            )
        munid = mun.objectID

        with freezegun.freeze_time('2001-01-02'):
            mun.delete()

        self.assertEquals(self._getregistrations(), [
            {
                'object': None,
                'objectID': munid,
                'registration_from': datetime.datetime(2001, 1, 1, 0, 0,
                                                       tzinfo=pytz.UTC),
                'registration_to': datetime.datetime(2001, 1, 2, 0, 0,
                                                     tzinfo=pytz.UTC),
            },
        ])

        with freezegun.freeze_time('2001-01-03'):
            mun = models.Municipality.objects.create(
                name='Aarhus',
                code=20,
                objectID=munid,
            )

        self.assertEquals(self._getregistrations(), [
            {
                # TODO: associate the registration with this object?
                'object': None,
                'objectID': munid,
                'registration_from': datetime.datetime(2001, 1, 1, 0, 0,
                                                       tzinfo=pytz.UTC),
                'registration_to': datetime.datetime(2001, 1, 2, 0, 0,
                                                     tzinfo=pytz.UTC),
            },
            {
                'object': mun.id,
                'objectID': munid,
                'registration_from': datetime.datetime(2001, 1, 3, 0, 0,
                                                       tzinfo=pytz.UTC),
                'registration_to': None
            },
        ])


@unittest.skipIf(os.getenv('SLOW_TESTS', '0') != '1', '$SLOW_TESTS not set')
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
            self.assertEquals(obj.code, int(val['POSTNR'].rstrip()))
            self.assertEquals(obj.name, val['POSTDISTRIKT'].rstrip())

    def test_import_b_number(self):
        for val in models.read_spreadsheet(self.fp):
            obj = models.BNumber.from_dict(val)
            self.assertEquals(obj.municipality.name, val['KOMNAVN'].rstrip())

    def test_import(self):
        models.import_spreadsheet(self.fp)
        self.assertEquals(len(models.Address.objects.all()), 22913)
