# -*- mode: python; coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals, print_function

from django.forms.models import model_to_dict
from django import test

# Create your tests here.
from . import models
from .models import Municipality


class CreationTests(test.TestCase):
    def setUp(self):
        mun = models.Municipality.objects.create(name='Aarhus', code=20)

        road = models.Road.objects.create(
            code=1337,
            name='Hans Hartvig Seedorffs Stræde',
            shortname='H. H. Seedorffs Stræde',
            dkName='Hans Hartvig Seedorffs Stræde',
            # this translation is quite likely horribly wrong
            glName='Hans Hartvig Seedorffs aqqusineq amitsoq',
            cprName='Hans Hartvig Seedorff\'s Street',
        )

        pc = models.PostalCode.objects.create(code=8000, name='Aarhus C')

        b = models.BNumber.objects.create(
            number=42,
            name='The Block',
            block='BS221B',
            municipality=mun,
        )

        self.addr = models.Address.objects.create(
            houseNumber='42Z',
            floor='Mezzanine',
            door='Up',
            locality=None,
            bNumber=b,
            road=road,
            postalCode=pc,
        )

    def test_addr(self):
        self.assertEquals(self.addr.bNumber.municipality.name, 'Aarhus')
        self.assertEquals(self.addr.bNumber.municipality.name, 'Aarhus')
        self.assertEquals(str(self.addr),
                          '42Z Hans Hartvig Seedorffs Stræde (1337)')
