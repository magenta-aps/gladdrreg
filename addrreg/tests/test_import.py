# -*- mode: python; coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals, print_function

import os

import openpyxl

from django import test
from django.conf import settings
from django.utils import translation

from ..management.commands import import_


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
