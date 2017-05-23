# -*- mode: python; coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals, print_function

import contextlib
import datetime
import io
import os
import sys
import unittest
import uuid

import freezegun
import openpyxl
import pycodestyle
import pytz

from django import apps, db, test
from django.conf import settings
from django.core import exceptions
from django.utils import six, translation

# Create your tests here.
from . import models
from .management.commands import import_

try:
    import selenium
except:
    selenium = None


DUMMY_DOMAIN = 'http://localhost'


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
                if dn != 'migrations' and not dn.startswith('venv-')
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

    def setUp(self):
        self.state = models.State.objects.create(
            id=0,
            state_id=0,
            name='Good',
            code=1,
        )

    def test_creation(self):
        mun = models.Municipality.objects.create(
            name='Aarhus',
            code=20,
            state=self.state,
            sumiffiik_domain=DUMMY_DOMAIN,
        )

        locality = models.Locality.objects.create(
            state=self.state,
            name='Somewhere',
            code=42,
            sumiffiik_domain=DUMMY_DOMAIN,
        )

        road = models.Road(
            municipality=mun,
            location=locality,
            state=self.state,
            code=1337,
            name='Hans Hartvig Seedorffs Stræde',
            shortname='H H Seedorffs Stræde',
            # this translation is quite likely horribly wrong
            alternate_name='H. H. Seedorffs aqqusineq amitsoq',
            cpr_name='Hans Hartvig Seedorff\'s Street',
            sumiffiik_domain=DUMMY_DOMAIN,
        )
        road.save()

        pc = models.PostalCode(
            state=self.state,
            code=8000,
            name='Aarhus C',
            sumiffiik_domain=DUMMY_DOMAIN,
        )
        pc.save()

        b = models.BNumber(
            municipality=mun,
            location=locality,
            state=self.state,
            code='42',
            name='The Block',
            nickname='BS221B',
            sumiffiik_domain=DUMMY_DOMAIN,
        )
        b.save()

        self.addr = models.Address(
            municipality=mun,
            state=self.state,
            house_number='42Z',
            floor='XX',
            room='42',
            b_number=b,
            road=road,
            sumiffiik_domain=DUMMY_DOMAIN,
        )
        self.addr.save()

        self.assertEquals(self.addr.b_number.municipality.name, 'Aarhus')
        self.assertEquals(self.addr.b_number.municipality.name, 'Aarhus')
        self.assertEquals(six.text_type(self.addr),
                          '42Z Hans Hartvig Seedorffs Stræde')

    @unittest.expectedFailure
    def test_create_duplicate_municipality_fails(self):
        """Test that creating two municipalities with the same code fails."""
        models.Municipality.objects.create(
            name='Aarhus',
            code=20,
            state=self.state,
            sumiffiik_domain=DUMMY_DOMAIN,
        )

        self.assertRaises(
            db.IntegrityError,
            models.Municipality.objects.create,
            name='Aarhus',
            code=20,
            sumiffiik_domain=DUMMY_DOMAIN,
            state=self.state,
        )


class TemporalTests(test.TransactionTestCase):
    reset_sequences = True

    @property
    def state(self):
        return models.State.objects.get_or_create(
            id=0,
            state_id=0,
            name='Good',
            code=1,
        )[0]

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
                state=self.state,
                sumiffiik_domain=DUMMY_DOMAIN,
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
                state=self.state,
                sumiffiik_domain=DUMMY_DOMAIN,
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
                              name='Aarhus', code=20, state=self.state,
                              sumiffiik_domain=DUMMY_DOMAIN)
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
                state=self.state,
                sumiffiik_domain=DUMMY_DOMAIN,
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
                state=self.state,
                sumiffiik_domain=DUMMY_DOMAIN,
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
                state=self.state,
                sumiffiik_domain=DUMMY_DOMAIN,
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
                           'Adropslagdata_20170510_datatotal.xlsx')

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.wb = openpyxl.load_workbook(cls.fixture, read_only=True,
                                        data_only=True)

    @classmethod
    def tearDownClass(cls):
        cls.wb.close()
        super().tearDownClass()

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

@unittest.skipIf(not selenium, 'selenium not installed')
class RightsTests(test.LiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        from selenium import webdriver
        from selenium.common import exceptions

        driver = getattr(webdriver, os.environ.get('BROWSER', 'Firefox'))

        if not driver:
            raise unittest.SkipTest('$BROWSER unset or invalid')

        try:
            cls.browser = driver()
        except Exception as exc:
            raise unittest.SkipTest(exc.args[0])

        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

        cls.browser.quit()

    def setUp(self):
        super().setUp()

        self.user_model = apps.apps.get_model(settings.AUTH_USER_MODEL)

        self.superuser = self.user_model.objects.create_superuser(
            'root', 'root@example.com', 'password',
        )

        self.state = models.State.objects.create(
            id=0,
            state_id=0,
            name='Good',
            code=1,
        )

        self.users = {}

        for l in ['A', 'B', 'C']:
            user = self.user_model.objects.create_user(
                'User' + l, 'user{}@example.com'.format(l), 'password',
                is_staff=True,
            )

            # don't grant the last user any rights
            if l < 'C':
                mun = models.Municipality.objects.create(
                    name='City ' + l, abbrev=l, code=ord(l),
                    state=self.state, sumiffiik_domain=DUMMY_DOMAIN,
                )

                rights = models.MunicipalityRights.objects.create(
                    municipality=mun,
                )
                rights.users.add(user)
                rights.save()

            self.users[user.username] = user

        self.browser.delete_all_cookies()

    def login(self, user):
        from selenium.webdriver.common.keys import Keys

        # logout
        self.browser.delete_all_cookies()
        self.browser.get(self.live_server_url + '/admin/logout/')
        self.browser.delete_all_cookies()
        self.browser.get(self.live_server_url)

        self.assertNotEqual(self.live_server_url, self.browser.current_url,
                            'logout failed!')

        # sanitity check the credentials
        self.client.logout()
        self.assertTrue(self.client.login(username=user, password='password'),
                        'login failed - invalid credentials!')


        self.browser.find_element_by_id("id_username").send_keys(
            user,
        )
        self.browser.find_element_by_id("id_password").send_keys(
            'password',
        )
        self.browser.find_element_by_css_selector("input[type=submit]").click()

        # wait for next page load
        self.browser.find_element_by_id("content")

        self.assertEquals(self.live_server_url + '/admin/',
                          self.browser.current_url,
                          'login failed')

    def get_user_modules(self, user, app):
        self.login(user)

        self.browser.get(self.live_server_url + '/admin')
        try:
            module = self.browser.find_element_by_css_selector(
                'div.app-addrreg.module'
            )
        except selenium.common.exceptions.NoSuchElementException:
            return None

        headers = module.find_elements_by_css_selector('th')

        return [header.text for header in headers]

    def test_user_memberships(self):
        with self.subTest('UserA'):
            self.assertTrue(self.users['UserA'].rights.exists())
            self.assertEquals(
                (self.users['UserA'].rights.all()
                 .values_list('municipality__name').get()),
                ('City A',),
            )

        with self.subTest('UserB'):
            self.assertTrue(self.users['UserB'].rights.exists())
            self.assertEquals(
                (self.users['UserB'].rights.all()
                 .values_list('municipality__name').get()),
                ('City B',),
            )

        self.assertFalse(self.users['UserC'].rights.exists())

    def test_module_list(self):
        user_modules = {
            'root': [
                'Addresses',
                'B-Numbers',
                'Districts',
                'Localities',
                'Municipalities',
                'Municipality Rights',
                'Postal Codes',
                'Roads',
                'States',
            ],

            'UserA': [ 'Addresses', 'B-Numbers', 'Roads' ],
            'UserB': [ 'Addresses', 'B-Numbers', 'Roads' ],
            'UserC': None,
        }

        for user, modules in user_modules.items():
            with self.subTest(user):
                self.assertEquals(
                    modules,
                    self.get_user_modules(user, 'addrreg'),
                )

