# -*- mode: python; coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals, print_function

import enumfields.admin
from django.contrib import admin
from django.db import models
from django.utils import six
from django.utils.translation import ugettext_lazy as _

from .base import BaseModel, AdminBase
from .temporal import TemporalModelBase

admin.site.disable_action('delete_selected')


class LocalityType(enumfields.IntEnum):
    UNKNOWN = 0
    TOWN = 1
    VILLAGE = 2
    STATION = 3
    AIRPORT = 4

    class Labels:
        UNKNOWN = _('Unknown')
        TOWN = _('Town')
        VILLAGE = _('Village')
        STATION = _('Station')
        AIRPORT = _('Airport')


@six.python_2_unicode_compatible
class Locality(six.with_metaclass(TemporalModelBase, BaseModel)):
    class Meta(object):
        verbose_name = _('Locality')
        verbose_name_plural = _('Localities')

        ordering = ('name',)

    # aka lokalitetskode
    code = models.IntegerField(_('Code'), db_index=True, unique=True)
    # aka lokalitetsnavn
    name = models.CharField(_('Name'), db_index=True, max_length=255)
    # aka lokalitetstype
    type = enumfields.EnumIntegerField(LocalityType, verbose_name=_('Type'),
                                       db_index=True,
                                       default=LocalityType.UNKNOWN)

    def __str__(self):
        return '{0.name} ({0.type})'.format(self)


@admin.register(Locality)
class LocalityAdmin(AdminBase):
    list_display = ('name', 'type', 'code',)
    list_filter = (('type', enumfields.admin.EnumFieldListFilter),)


@six.python_2_unicode_compatible
class Municipality(six.with_metaclass(TemporalModelBase, BaseModel)):
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


@admin.register(Municipality)
class MunicipalityAdmin(AdminBase):
    list_display = ('name', 'code',)


@six.python_2_unicode_compatible
class PostalCode(six.with_metaclass(TemporalModelBase, BaseModel)):
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


@admin.register(PostalCode)
class PostalCodeAdmin(AdminBase):
    list_display = ('name', 'code',)


@six.python_2_unicode_compatible
class Road(six.with_metaclass(TemporalModelBase, BaseModel)):
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


@admin.register(Road)
class RoadAdmin(AdminBase):
    list_display = ('name', 'code')
    search_fields = ('name',)


@six.python_2_unicode_compatible
class BNumber(six.with_metaclass(TemporalModelBase, BaseModel)):
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

    municipality = models.ForeignKey(Municipality, models.PROTECT,
                                     verbose_name=_('Municipality'),
                                     null=False, blank=True, db_index=True)

    def __str__(self):
        parts = [self.number]
        if self.block:
            parts += [' - ']
        if self.name:
            parts += [' (', self.name, ')']

        return ''.join(parts)


@admin.register(BNumber)
class BNumberAdmin(AdminBase):
    list_display = ('number', 'name', 'block', 'municipality',)
    list_filter = ('municipality',)
    search_fields = ('=number', '=name', '=block')


@six.python_2_unicode_compatible
class Address(six.with_metaclass(TemporalModelBase, BaseModel)):
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

    locality = models.ForeignKey(Locality, models.CASCADE,
                                 verbose_name=_('Locality'),
                                 null=True, blank=True)
    bNumber = models.ForeignKey(BNumber, models.SET_NULL,
                                verbose_name=_('B-Number'),
                                null=True, blank=True)
    road = models.ForeignKey(Road, models.CASCADE,
                             verbose_name=_('Road'),
                             null=True, blank=True)
    postalCode = models.ForeignKey(PostalCode, models.PROTECT,
                                   verbose_name=_('Postal Code'),
                                   null=True, blank=True)

    def __str__(self):
        # Translators: Human-readable description of an Address
        return _('{0.houseNumber} {0.road}').format(self)


@admin.register(Address)
class AddressAdmin(AdminBase):
    list_display = ('road', 'houseNumber', 'floor', 'door', 'postalCode',
                    'bNumber',)
    list_filter = ('locality', 'postalCode')
    search_fields = ('road__name', 'postalCode__name', 'locality__name')
