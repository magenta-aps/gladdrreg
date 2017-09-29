# -*- mode: python; coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals, print_function

import datetime

import freezegun
import pytz

from django import test
from django.core import exceptions

from .. import models
from .util import DUMMY_DOMAIN


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
        self.assertEquals(models.Municipality.objects.count(), 1)

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
