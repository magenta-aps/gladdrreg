# -*- mode: python; coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals, print_function

import enum

import enumfields
from django import forms
from django.conf import settings
from django.contrib import admin
from django.core import exceptions
from django.db import models
from django.utils.translation import ugettext_lazy as _

from . import base, temporal, events

admin.site.disable_action('delete_selected')


class MunicipalityValidatingForm(base.FormBase):

    def clean(self):
        cleaned_data = super().clean()

        municipalities = {
            key: getattr(val, 'municipality', val)
            for key, val in cleaned_data.items()
            if hasattr(val, 'municipality') or key == 'municipality'
        }

        if len(set(municipalities.values())) > 1:
            for field, municipality in municipalities.items():
                self.add_error(field,
                               forms.ValidationError(
                                   _('Fields cannot be in different '
                                     'municipalities; this one is in “%s”!'),
                                   params=municipality,
                               ))

        return cleaned_data


class State(base.AbstractModel, metaclass=temporal.TemporalModelBase):

    class Meta(object):
        verbose_name = _('State')
        verbose_name_plural = _('States')

        ordering = ('code',)
        default_permissions = ()

    state = models.ForeignKey('addrreg.State', models.DO_NOTHING,
                              verbose_name=_('State'), db_index=True,
                              related_name='+')

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

    fieldsets = (
        (None, {
            'fields': ('code', 'name', 'active'),
            'classes': ('wide', 'extra_pretty'),
        }),
    ) + base.AdminBase._fieldsets


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

    @staticmethod
    def get_objecttype_names():
        return ['localitytype']


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

    sumiiffik = base.SumiiffikIDField(null=True)
    sumiiffik_domain = base.SumiiffikDomainField(
        default='https://data.gl/najugaq/municipality/v1',
    )

    code = models.PositiveSmallIntegerField(_('Code'), db_index=True)

    abbrev = models.CharField(_('Abbreviation'), max_length=4, db_index=True)
    name = models.CharField(_('Name'), max_length=60, db_index=True)

    def __str__(self):
        return self.name


@admin.register(Municipality)
class MunicipalityAdmin(base.AdminBase):
    list_display = ('abbrev', 'name', 'state', 'active')

    fieldsets = (
        (_('Info'), {
            'fields': ('name', 'abbrev', 'code'),
            'classes': ('wide',),
        }),
        (_('Geography'), {
            'fields': ('sumiiffik', 'sumiiffik_domain'),
            'classes': ('wide',),
        }),
    ) + base.AdminBase._fieldsets


class District(base.AbstractModel,
               metaclass=temporal.TemporalModelBase):

    class Meta(object):
        verbose_name = _('District')
        verbose_name_plural = _('Districts')

        ordering = ('abbrev',)
        default_permissions = ()

    sumiiffik = base.SumiiffikIDField()
    sumiiffik_domain = base.SumiiffikDomainField(
        default='https://data.gl/najugaq/district/v1',
    )

    code = models.PositiveSmallIntegerField(_('Code'),
                                            db_index=True, null=True)

    abbrev = models.CharField(_('Abbreviation'), max_length=4, db_index=True)
    name = models.CharField(_('Name'), max_length=60, db_index=True)

    def __str__(self):
        return self.name


@admin.register(District)
class DistrictAdmin(base.AdminBase):
    list_display = ('abbrev', 'name', 'state', 'active')

    search_fields = ('=code', 'name', '=abbrev')

    fieldsets = (
        (_('Info'), {
            'fields': ('name', 'abbrev', 'code'),
            'classes': ('wide',),
        }),
        (_('Geography'), {
            'fields': ('sumiiffik', 'sumiiffik_domain'),
            'classes': ('wide',),
        }),
    ) + base.AdminBase._fieldsets


class PostalCode(base.AbstractModel,
                 metaclass=temporal.TemporalModelBase):

    class Meta(object):
        verbose_name = _('Postal Code')
        verbose_name_plural = _('Postal Codes')

        ordering = ('code',)
        default_permissions = ()

    sumiiffik = base.SumiiffikIDField()
    sumiiffik_domain = base.SumiiffikDomainField(
        default='https://data.gl/najugaq/postalcode/v1',
    )

    # aka postnummer
    code = models.PositiveSmallIntegerField(_('Number'),
                                            db_index=True, unique=True)
    # aka by
    name = models.CharField(_('City'), db_index=True, max_length=60)

    def __str__(self):
        # Translators: Human-readable description of a PostalCode
        return _('{0.code} {0.name}').format(self)

    @classmethod
    def alias_names(cls):
        return ['postnr']


@admin.register(PostalCode)
class PostalCodeAdmin(base.AdminBase):
    list_display = ('code', 'name', 'state', 'active')

    fieldsets = (
        (_('Info'), {
            'fields': ('code', 'name'),
            'classes': ('wide',),
        }),
        (_('Geography'), {
            'fields': ('sumiiffik', 'sumiiffik_domain'),
            'classes': ('wide',),
        }),
    ) + base.AdminBase._fieldsets


class Locality(base.AbstractModel,
               metaclass=temporal.TemporalModelBase):

    class Meta(object):
        verbose_name = _('Locality')
        verbose_name_plural = _('Localities')

        ordering = ('abbrev',)
        default_permissions = ()

    sumiiffik = base.SumiiffikIDField()
    sumiiffik_domain = base.SumiiffikDomainField(
        default='https://data.gl/najugaq/locality/v1',
    )

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
        'state',
        'active',
    )

    list_filter = (
        'municipality',
        'district',
        'type',
        'locality_state',
    ) + base.AdminBase.list_filter

    superuser_only = True

    fieldsets = (
        (_('Info'), {
            'fields': ('name', 'abbrev', 'code', 'type', 'locality_state'),
            'classes': ('wide',),
        }),
        (_('Geography'), {
            'fields': (
                'municipality', 'district', 'postal_code',
                'sumiiffik', 'sumiiffik_domain',
            ),
            'classes': ('wide',),
        }),
    ) + base.AdminBase._fieldsets


class BNumber(base.AbstractModel,
              metaclass=temporal.TemporalModelBase):

    class Meta(object):
        verbose_name = _('B-Number')
        verbose_name_plural = _('B-Numbers')

        default_permissions = ()

    sumiiffik = base.SumiiffikIDField()
    sumiiffik_domain = base.SumiiffikDomainField(
        default='https://data.gl/najugaq/number/v1',
    )

    code = models.CharField(_('B-Number'),
                            db_index=True, null=True, max_length=8)

    # aka kaldenavn
    b_type = models.CharField(_('B-Type'), max_length=60, null=True, blank=True)
    # aka blokbetegnelse
    b_callname = models.CharField(_('B-Nickname'), max_length=60,
                                blank=True, null=True)

    location = base.ForeignKey(Locality, verbose_name=_('Locality'),
                               null=False)
    municipality = base.ForeignKey(Municipality, verbose_name=_('Municipality'),
                                   null=False)

    def __str__(self):
        parts = [self.code]
        if self.b_callname:
            parts += [' (', self.b_callname, ')']

        return ''.join(parts)

    @classmethod
    def alias_names(cls):
        return ['bnr']


@admin.register(BNumber)
class BNumberAdmin(base.AdminBase):
    form = MunicipalityValidatingForm

    list_display = (
        'code',
        'b_type',
        'municipality',
        'location',
        'state',
        'active',
    )
    search_fields = ('=code', 'b_type', 'municipality__name', 'location__name')

    list_filter = (
        'location',
        'municipality',
    ) + base.AdminBase.list_filter

    fieldsets = (
        (_('Info'), {
            'fields': ('code', 'b_callname', 'b_type'),
            'classes': ('wide',),
        }),
        (_('Geography'), {
            'fields': (
                'municipality', 'location',
                'sumiiffik', 'sumiiffik_domain',
            ),
            'classes': ('wide',),
        }),
    ) + base.AdminBase._fieldsets


class Road(base.AbstractModel,
           metaclass=temporal.TemporalModelBase):

    class Meta(object):
        verbose_name = _('Road')
        verbose_name_plural = _('Roads')

        ordering = ('name',)
        default_permissions = ()

    sumiiffik = base.SumiiffikIDField()
    sumiiffik_domain = base.SumiiffikDomainField(
        default='https://data.gl/najugaq/road/v1',
    )

    code = models.PositiveIntegerField(_('Code'), db_index=True)
    name = models.CharField(_('Name'), db_index=True, max_length=34)

    shortname = models.CharField(_('Abbreviated Name'), max_length=20,
                                 help_text=_('20 character maximum'),
                                 blank=True, null=True)

    alternate_name = models.CharField(_('Alternate Name'), max_length=34,
                                      blank=True, null=True)
    cpr_name = models.CharField(_('CPR Name'), max_length=34,
                                blank=True, null=True)

    location = base.ForeignKey(Locality, _('Locality'))
    municipality = base.ForeignKey(Municipality, _('Municipality'))

    def __str__(self):
        return self.name+" ("+str(self.code)+")"


@admin.register(Road)
class RoadAdmin(base.AdminBase):
    form = MunicipalityValidatingForm

    list_display = ('name', 'location', 'code', 'state', 'active')
    list_filter = (
        'municipality',
        'location',
    ) + base.AdminBase.list_filter

    search_fields = (
        '=code',
        'name',
        'shortname',
        'alternate_name',
        'cpr_name',
        'location__name',
        'municipality__name',
    )

    fieldsets = (
        (_('Info'), {
            'fields': (
                'name', 'code',
                'shortname', 'alternate_name', 'cpr_name',
            ),
            'classes': ('wide',),
        }),
        (_('Geography'), {
            'fields': (
                'sumiiffik', 'sumiiffik_domain',
                'location', 'municipality',
            ),
            'classes': ('wide',),
        }),
    ) + base.AdminBase._fieldsets


class Address(base.AbstractModel,
              metaclass=temporal.TemporalModelBase):

    class Meta(object):
        verbose_name = _('Address')
        verbose_name_plural = _('Addresses')

        ordering = 'road',
        default_permissions = ()

    sumiiffik = base.SumiiffikIDField()
    sumiiffik_domain = base.SumiiffikDomainField(
        default='https://data.gl/najugaq/address/v1',
    )

    # aka husnummer
    house_number = models.CharField(_('House Number'), max_length=6,
                                    null=True, blank=True)
    # aka etage
    floor = models.CharField(_('Floor'), max_length=2,
                             null=True, blank=True)
    # aka sidedør
    room = models.CharField(_('Room'), max_length=6,
                            null=True, blank=True)

    b_number = base.ForeignKey(BNumber, _('B-Number'))
    road = base.ForeignKey(Road, _('Road'))
    municipality = base.ForeignKey(Municipality, _('Municipality'))

    def location(self):
        return self.road.location

    location.short_description = _('Locality')

    def __str__(self):
        if self.floor:
            if self.room:
                return (
                    '{0.house_number} {0.road}, {0.floor}, {0.room}'
                ).format(self)
            else:
                return (
                    '{0.house_number} {0.road}, {0.floor}'
                ).format(self)
        elif self.house_number:
            return _('{0.house_number} {0.road}').format(self)
        else:
            return _('{0.road}').format(self)


@admin.register(Address)
class AddressAdmin(base.AdminBase):
    form = MunicipalityValidatingForm

    related_search_fields = {
        'b_number': ('code', 'b_type', 'b_callname'),
    }

    list_display = (
        'road',
        'house_number',
        'floor',
        'room',
        'location',
        'municipality',
        'state',
        'active',
    )

    readonly_fields = ('location',)

    list_filter = (
        'road__location__name',
        'municipality',
    ) + base.AdminBase.list_filter

    search_fields = (
        'road__name',
        'house_number',
        'municipality__name',
    )

    fieldsets = (
        (_('Info'), {
            'fields': (
                'road', 'house_number', 'floor', 'room', 'b_number',
            ),
            'classes': ('wide',),
        }),
        (_('Geography'), {
            'fields': (
                'sumiiffik', 'sumiiffik_domain',
                'location', 'municipality',
            ),
            'classes': ('wide',),
        }),
    ) + base.AdminBase._fieldsets


class MunicipalityRights(models.Model):

    class Meta:
        verbose_name = _('Municipality Rights')
        verbose_name_plural = _('Municipality Rights')

        default_permissions = ()

    municipality = models.OneToOneField(
        'Municipality', models.CASCADE,
        verbose_name=_('Municipality'),
        related_name='rights',
    )
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        verbose_name=_('Users'),
        related_name='rights',
    )

    def __str__(self):
        return self.municipality.name


admin.site.register(MunicipalityRights)
