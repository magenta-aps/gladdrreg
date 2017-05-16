# -*- mode: python; coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals, print_function

import enum

import enumfields
from django import forms
from django.conf import settings
from django.contrib import admin
from django.db import models
from django.utils.translation import ugettext_lazy as _

from . import base, temporal

admin.site.disable_action('delete_selected')


class State(base.AbstractModel, metaclass=temporal.TemporalModelBase):
    class Meta(object):
        verbose_name = _('State')
        verbose_name_plural = _('States')

        ordering = ('code',)
        default_permissions = ()

    code = models.PositiveSmallIntegerField(_('Code'), db_index=True,
                                            unique=True)
    name = models.CharField(_('Name'), max_length=20, null=True)
    description = models.CharField(_('Description'), max_length=60,
                                   blank=True)

    def __str__(self):
        return self.name or '-'


@admin.register(State)
class StateAdmin(base.AdminBase):
    list_display = ('name', 'description', 'state', 'active')


@enum.unique
class LocalityType(enumfields.IntEnum):
    '''
    http://www.stat.gl/publ/da/be/201401/pdf/Lokaliteter%20i%20Grønland.pdf
    '''
    UNKNOWN = 0
    TOWN = 1
    SETTLEMENT = 2
    MINE = 3
    STATION = 5
    AIRPORT = 6
    FARM = 7
    DEVELOPMENT = 8

    class Labels:
        UNKNOWN = _('Unknown')
        TOWN = _('Town')
        SETTLEMENT = _('Settlement')
        MINE = _('Mine')
        STATION = _('Station')
        AIRPORT = _('Airport')
        FARM = _('Farm')
        DEVELOPMENT = _('Development')


@enum.unique
class LocalityState(enumfields.IntEnum):
    '''
    http://www.stat.gl/publ/da/be/201401/pdf/Lokaliteter%20i%20Grønland.pdf
    '''
    PROJECTED = 10
    ACTIVE = 15
    ABANDONED = 20

    class Labels:
        PROJECTED = _('Projected')
        ACTIVE = _('Active')
        ABANDONED = _('Abandoned')


class Municipality(base.AbstractModel,
                   metaclass=temporal.TemporalModelBase):
    class Meta(object):
        verbose_name = _('Municipality')
        verbose_name_plural = _('Municipalities')

        ordering = ('abbrev',)
        default_permissions = ()

    sumiffiik = base.SumiffiikIDField(null=True)
    sumiffiik_domain = base.SumiffiikDomainField()

    code = models.PositiveSmallIntegerField(_('Code'), db_index=True)

    abbrev = models.CharField(_('Abbreviation'), max_length=4, db_index=True)
    name = models.CharField(_('Name'), max_length=60, db_index=True)

    def __str__(self):
        return self.name


@admin.register(Municipality)
class MunicipalityAdmin(base.AdminBase):
    list_display = ('abbrev', 'name', 'state', 'active')


class District(base.AbstractModel,
               metaclass=temporal.TemporalModelBase):
    class Meta(object):
        verbose_name = _('District')
        verbose_name_plural = _('Districts')

        ordering = ('abbrev',)
        default_permissions = ()

    sumiffiik = base.SumiffiikIDField()
    sumiffiik_domain = base.SumiffiikDomainField()

    code = models.PositiveSmallIntegerField(_('Code'),
                                            db_index=True, null=True)

    abbrev = models.CharField(_('Abbreviation'), max_length=4, db_index=True)
    name = models.CharField(_('Name'), max_length=60, db_index=True)

    def __str__(self):
        return self.name


@admin.register(District)
class DistrictAdmin(base.AdminBase):
    list_display = ('abbrev', 'name', 'state', 'active')


class PostalCode(base.AbstractModel,
                 metaclass=temporal.TemporalModelBase):
    class Meta(object):
        verbose_name = _('Postal Code')
        verbose_name_plural = _('Postal Codes')

        ordering = ('code',)
        default_permissions = ()

    sumiffiik = base.SumiffiikIDField()
    sumiffiik_domain = base.SumiffiikDomainField()

    # aka postnummer
    code = models.PositiveSmallIntegerField(_('Number'),
                                            db_index=True, unique=True)
    # aka by
    name = models.CharField(_('City'), db_index=True, max_length=60)

    def __str__(self):
        # Translators: Human-readable description of a PostalCode
        return _('{0.code} {0.name}').format(self)


@admin.register(PostalCode)
class PostalCodeAdmin(base.AdminBase):
    list_display = ('name', 'code', 'state', 'active')


class Locality(base.AbstractModel,
               metaclass=temporal.TemporalModelBase):
    class Meta(object):
        verbose_name = _('Locality')
        verbose_name_plural = _('Localities')

        ordering = ('abbrev',)
        default_permissions = ()

    sumiffiik = base.SumiffiikIDField()
    sumiffiik_domain = base.SumiffiikDomainField()

    code = models.PositiveSmallIntegerField(_('Code'),
                                            db_index=True, null=True)

    abbrev = models.CharField(_('Abbreviation'), max_length=4, null=True,
                              db_index=True)
    name = models.CharField(_('Name'), max_length=60,
                            db_index=True)

    type = enumfields.EnumIntegerField(LocalityType, verbose_name=_('Type'),
                                       db_index=True,
                                       default=LocalityType.UNKNOWN)
    locality_state = enumfields.EnumIntegerField(
        LocalityState, verbose_name=_('Locality State'),
        default=LocalityState.PROJECTED, db_index=True,
    )
    municipality = base.ForeignKey(Municipality, _('Municipality'),
                                   null=True, blank=True)
    district = base.ForeignKey(District, _('District'),
                               null=True, blank=True)
    postal_code = base.ForeignKey(PostalCode, _('Postal Code'),
                                  null=True, blank=True)

    def __str__(self):
        # Translators: Human-readable description of a Locality
        return _('{0.name} ({0.type.label})').format(self)


@admin.register(Locality)
class LocalityAdmin(base.AdminBase):
    list_display = (
        'abbrev',
        'name',
        'type',
        'locality_state',
    )

    list_filter = (
                      'municipality',
                      'district',
                      'type',
                      'locality_state',
                  ) + base.AdminBase.list_filter


class BNumber(base.AbstractModel,
              metaclass=temporal.TemporalModelBase):
    class Meta(object):
        verbose_name = _('B-Number')
        verbose_name_plural = _('B-Numbers')

        default_permissions = ()

    sumiffiik = base.SumiffiikIDField()
    sumiffiik_domain = base.SumiffiikDomainField()

    code = models.CharField(_('Code'), db_index=True, null=True, max_length=8)

    # aka kaldenavn
    name = models.CharField(_('Name'), max_length=60, null=True)
    # aka blokbetegnelse
    nickname = models.CharField(_('Nickname'), max_length=60, null=True)

    location = base.ForeignKey(Locality, verbose_name=_('Locality'), null=False)
    municipality = base.ForeignKey(Municipality, _('Municipality'), null=False)

    def __str__(self):
        parts = [self.code]
        if self.name:
            parts += [' (', self.name, ')']

        return ''.join(parts)


@admin.register(BNumber)
class BNumberAdmin(base.AdminBase):
    list_display = (
        'code',
        'name',
        'municipality',
        'location',
    )
    search_fields = ('=code', '=name', '=municipality' '=location')

    list_filter = (
        'location',
        'municipality',
    ) + base.AdminBase.list_filter


class Road(base.AbstractModel,
           metaclass=temporal.TemporalModelBase):
    class Meta(object):
        verbose_name = _('Road')
        verbose_name_plural = _('Roads')

        ordering = ('name',)
        default_permissions = ()

    sumiffiik = base.SumiffiikIDField()
    sumiffiik_domain = base.SumiffiikDomainField()

    code = models.PositiveIntegerField(_('Code'), db_index=True)
    name = models.CharField(_('Name'), db_index=True, max_length=34)

    shortname = models.CharField(_('Abbreviated Name'), max_length=20,
                                 null=True)

    alternate_name = models.CharField(_('Alternate Name'), max_length=34,
                                      null=True)
    cpr_name = models.CharField(_('CPR Name'), max_length=34, null=True)

    location = base.ForeignKey(Locality, _('Locality'))
    municipality = base.ForeignKey(Municipality, _('Municipality'))

    def __str__(self):
        return self.name


@admin.register(Road)
class RoadAdmin(base.AdminBase):
    list_display = ('name', 'code')
    search_fields = ('name',)


class Address(base.AbstractModel,
              metaclass=temporal.TemporalModelBase):
    class Meta(object):
        verbose_name = _('Address')
        verbose_name_plural = _('Addresses')

        ordering = 'road',
        default_permissions = ()

    sumiffiik = base.SumiffiikIDField()
    sumiffiik_domain = base.SumiffiikDomainField()

    # aka husnummer
    house_number = models.CharField(_('House Number'), max_length=6,
                                    null=True, blank=True)
    # aka etage
    floor = models.CharField(_('Floor'), max_length=2,
                             null=True, blank=True)
    # aka sidedør
    room = models.CharField(_('Room'), max_length=6,
                            null=True, blank=True)

    b_number = base.ForeignKey(BNumber, _('B-Number'), null=True, blank=True)
    road = base.ForeignKey(Road, _('Road'), null=True, blank=True)
    municipality = base.ForeignKey(Municipality, _('Municipality'),
                                   null=False, blank=True)

    def __str__(self):
        # Translators: Human-readable description of an Address
        return _('{0.house_number} {0.road}').format(self)


@admin.register(Address)
class AddressAdmin(base.AdminBase):
    list_display = (
        'road',
        'house_number',
        'floor',
        'room',
        'municipality',
    )
    list_filter = (
        'municipality',
    ) + base.AdminBase.list_filter
    search_fields = (
        'road__name',
        'municipality__name',
        'locality__name',
    )
