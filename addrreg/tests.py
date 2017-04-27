# -*- mode: python; coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals, print_function

import contextlib
import datetime
import io

import freezegun
import openpyxl
import os
import pycodestyle
import pytz
from django import db, test
from django.conf import settings
from django.core import exceptions
from django.utils import six, translation

# Create your tests here.
from . import models
from .management.commands import import_


class CodeStyleTests(test.SimpleTestCase):
    @property
    def rootdir(self):
        return os.path.dirname(os.path.dirname(__file__))

    @property
    def source_files(self):
        """Generator that yields Python sources to test"""

        for dirpath, dirs, fns in os.walk(self.rootdir):
            dirs[:] = [
                dn for dn in dirs
                if dn != 'migrations' and not dn.startswith('pyenv-')
            ]

            for fn in fns:
                if fn[0] != '.' and fn.endswith('.py'):
                    yield os.path.join(dirpath, fn)

    def test_pep8(self):
        pep8style = pycodestyle.StyleGuide()
        pep8style.init_report(pycodestyle.StandardReport)

        buf = io.StringIO()

        with contextlib.redirect_stdout(buf):
            for fn in self.source_files:
                pep8style.check_files([fn])

        assert not buf.getvalue(), \
            "Found code style errors and/or warnings:\n\n" + buf.getvalue()

    def test_source_files(self):
        sources = list(self.source_files)
        self.assert_(sources)
        self.assertGreater(len(sources), 1, sources)


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


class VerifyImport(test.SimpleTestCase):
    fixture = os.path.join(settings.BASE_DIR, 'fixtures',
                           'Adropslagdata_20170423_datatotal.xlsx')

    @classmethod
    def setUpClass(cls):
        cls.wb = openpyxl.load_workbook(cls.fixture, read_only=True,
                                        data_only=True)

    @classmethod
    def tearDownClass(cls):
        cls.wb.close()

    def _get_sheet(self, name):
        sheet = self.wb[name]

        rows = sheet.rows
        header_row = next(rows)

        return [
            {
                header_row[i].value: cell.value
                for i, cell in enumerate(row)
            }
            for row in rows
        ]

    @translation.override('da')
    def test_locality_type(self):
        for t in self._get_sheet('localitytype'):
            e = import_.VALUE_MAPS['type'][t['UID']]

            self.assertEquals(t['type'], str(e.label))
            self.assertEquals(t['code'], e.value)

    @translation.override('da')
    def test_locality_state(self):
        for t in self._get_sheet('localitystate'):
            e = import_.VALUE_MAPS['locality_state'][t['UID']]

            self.assertEquals(t['stateda'], str(e.label))
            self.assertEquals(t['code'], e.value)
