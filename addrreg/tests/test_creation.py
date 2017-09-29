# -*- mode: python; coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals, print_function

from django import test

from .. import models
from .util import DUMMY_DOMAIN


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
            b_callname='The Block',
            b_type='BS221B',
            sumiffiik_domain=DUMMY_DOMAIN,
        )
        b.save()

        self.addr = models.Address(
            municipality=mun,
            state=self.state,
            house_number='42Z',
            floor='13',
            room='mf',
            b_number=b,
            road=road,
            sumiffiik_domain=DUMMY_DOMAIN,
        )
        self.addr.save()

        self.assertEquals(self.addr.b_number.municipality.name, 'Aarhus')
        self.assertEquals(self.addr.b_number.municipality.name, 'Aarhus')
        self.assertEquals(str(self.addr),
                          '42Z Hans Hartvig Seedorffs Stræde (1337), 13, mf')
