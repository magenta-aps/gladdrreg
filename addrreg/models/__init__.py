# -*- mode: python; coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals, print_function

import openpyxl
import six
from django.contrib import admin
from django.db import models
from django.utils.translation import ugettext_lazy as _

from .base import BaseModel, AdminBase

admin.site.disable_action('delete_selected')


@six.python_2_unicode_compatible
class Locality(BaseModel):

    class Meta(object):
        verbose_name = _('Locality')
        verbose_name_plural = _('Localities')

        ordering = ('name',)

    # aka lokalitetskode
    code = models.IntegerField(_('Code'), db_index=True, unique=True)
    # aka lokalitetsnavn
    name = models.CharField(_('Name'), db_index=True, max_length=255)
    # aka lokalitetstype
    type = models.CharField(_('Type'), db_index=True, max_length=255)

    def __str__(self):
        return '{0.name} ({0.type})'.format(self)

    @classmethod
    def from_dict(cls, vals):
        code = vals['LOKALITETSNR']
        if not code or not code.strip():
            return None

        obj, created = cls.objects.get_or_create(
            code=code,
            defaults={
                'name': vals['LOKALITETSNAVN'].rstrip(),
                'type': vals['LOKALITETS_TYPE_NAVN'].rstrip(),
            }
        )

        return obj


@admin.register(Locality)
class LocalityAdmin(AdminBase):
    list_display = ('name', 'type', 'code',)


@six.python_2_unicode_compatible
class Municipality(BaseModel):

    class Meta(object):
        verbose_name = _('Municipality')
        verbose_name_plural = _('Municipalities')

        ordering = ('name',)

    # aka kommunekode
    code = models.PositiveSmallIntegerField(_('Code'),
                                            db_index=True, unique=True)
    # aka kommunenavn
    name = models.CharField(_('Name'), max_length=255)

    def __str__(self):
        if self.name.strip() == 'uk':
            return '{} {}'.format(self.name, self.code)
        else:
            return self.name

    @classmethod
    def from_dict(cls, vals):
        obj, created = cls.objects.get_or_create(
            code=vals['KOMMUNEKODE'],
            defaults={
                'name': vals['KOMNAVN'].rstrip(),
            }
        )

        return obj


@admin.register(Municipality)
class MunicipalityAdmin(AdminBase):
    list_display = ('name', 'code',)


@six.python_2_unicode_compatible
class PostalCode(BaseModel):

    class Meta(object):
        verbose_name = _('Postal Code')
        verbose_name_plural = _('Postal Codes')

        ordering = ('code',)

    # aka postnummer
    code = models.PositiveSmallIntegerField(_('Number'),
                                            db_index=True, unique=True)
    # aka by
    name = models.CharField(_('City'), db_index=True, max_length=255)

    def __str__(self):
        # Translators: Human-readable description of a PostalCode
        return _('{0.code} {0.name}').format(self)

    @classmethod
    def from_dict(cls, vals):
        obj, created = cls.objects.get_or_create(
            code=int(vals['POSTNR']),
            defaults={
                'name': vals['POSTDISTRIKT'].rstrip(),
            }
        )

        return obj


@admin.register(PostalCode)
class PostalCodeAdmin(AdminBase):
    list_display = ('name', 'code',)


@six.python_2_unicode_compatible
class Road(BaseModel):

    class Meta(object):
        verbose_name = _('Road')
        verbose_name_plural = _('Roads')

        ordering = ('name',)

    # aka vejkode
    code = models.PositiveIntegerField(_('Code'), db_index=True, unique=True)
    # aka vejnavn
    name = models.CharField(_('Name'), db_index=True, max_length=255)

    # aka forkortetnavn_20_tegn
    shortname = models.CharField(_('Abbreviated Name'), max_length=20)

    # aka dansk_navn
    dkName = models.CharField(_('Danish Name'), max_length=255)
    # aka grønlandsk_navn
    glName = models.CharField(_('Greenlandic Name'), max_length=255, )
    # aka cpr_navn
    cprName = models.CharField(_('CPR Name'), max_length=255)

    def __str__(self):
        return self.name

    @classmethod
    def from_dict(cls, vals):
        obj, created = cls.objects.get_or_create(
            code=vals['VEJKODE'],
            defaults={
                'name': vals['VEJNAVN'].rstrip(),
            }
        )

        return obj


@admin.register(Road)
class RoadAdmin(AdminBase):
    list_display = ('name', 'code')
    search_fields = ('name',)


@six.python_2_unicode_compatible
class BNumber(BaseModel):

    class Meta(object):
        verbose_name = _('B-Number')
        verbose_name_plural = _('B-Numbers')

        ordering = ('number',)

    # aka nummer
    number = models.CharField(_('Number'), db_index=True,
                              max_length=255)
    # aka kaldenavn
    name = models.CharField(_('Nickname'), max_length=255)
    # aka blokbetegnelse
    block = models.CharField(_('Block Designation'), max_length=255)

    municipality = models.ForeignKey(Municipality,
                                     verbose_name=_('Municipality'),
                                     null=False, blank=True, db_index=True)

    def __str__(self):
        parts = [self.number]
        if self.block:
            parts += [' - ']
        if self.name:
            parts += [' (', self.name, ')']

        return ''.join(parts)

    @classmethod
    def from_dict(cls, vals):
        obj, created = cls.objects.get_or_create(
            number=vals['BNR'],
            municipality=Municipality.from_dict(vals),
        )

        return obj


@admin.register(BNumber)
class BNumberAdmin(AdminBase):
    list_display = ('number', 'name', 'block', 'municipality',)
    list_filter = ('municipality',)
    search_fields = ('=number', '=name', '=block')


@six.python_2_unicode_compatible
class Address(BaseModel):

    class Meta(object):
        verbose_name = _('Address')
        verbose_name_plural = _('Addresses')

        ordering = 'road',

    # aka husnummer
    houseNumber = models.CharField(_('House Number'), max_length=255,
                                   blank=True)
    # aka etage
    floor = models.CharField(_('Floor'), max_length=255, blank=True)
    # aka sidedør
    door = models.CharField(_('Door'), max_length=255, blank=True)

    locality = models.ForeignKey(Locality,
                                 verbose_name=_('Locality'),
                                 null=True, blank=True)
    bNumber = models.ForeignKey(BNumber,
                                verbose_name=_('B-Number'),
                                null=True, blank=True)
    road = models.ForeignKey(Road,
                             verbose_name=_('Road'),
                             null=True, blank=True)
    postalCode = models.ForeignKey(PostalCode,
                                   verbose_name=_('Postal Code'),
                                   null=True, blank=True)

    def __str__(self):
        # i18n: Human-readable description of an Address
        return _('{0.houseNumber} {0.road}').format(self)

    @classmethod
    def from_dict(cls, vals):
        return cls.objects.create(
            houseNumber=vals['HUSNR'] or '',
            floor=vals['ETAGE'] or '',
            door=vals['SIDE'] or '',
            locality=Locality.from_dict(vals),
            bNumber=BNumber.from_dict(vals),
            road=Road.from_dict(vals),
            postalCode=PostalCode.from_dict(vals)
        )


@admin.register(Address)
class AddressAdmin(AdminBase):
    list_display = ('road', 'houseNumber', 'floor', 'door', 'postalCode',
                    'bNumber',)
    list_filter = ('locality', 'postalCode')
    search_fields = ('road__name', 'postalCode__name', 'locality__name')


def read_spreadsheet(fp):
    wb = openpyxl.load_workbook(fp, read_only=True, data_only=True)
    rows = wb.active.rows

    column_names = {
        cellidx: cell.value for cellidx, cell in
        enumerate(next(rows))
    }

    for row in rows:
        r = {
            column_names[cellidx]: cell.value
            for cellidx, cell in enumerate(row)
        }
        if any(r.values()):
            yield r


def import_spreadsheet(fp):
    for row in read_spreadsheet(fp):
        Address.from_dict(row)
