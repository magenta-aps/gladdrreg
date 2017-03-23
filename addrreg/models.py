# -*- mode: python; coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals, print_function

import uuid

from django.contrib import admin
from django.core import serializers
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.template import engines

admin.site.disable_action('delete_selected')

class BaseModel(models.Model):
    '''
    Abstract BaseModel class specifying a unique object.
    '''

    class Meta(object):
        abstract = True

    # aka sumiffiik
    objectID = models.UUIDField(primary_key=True,
                                default=uuid.uuid4,
                                editable=False,
                                verbose_name=_('Object ID'))

    def __repr__(self):
        return '<{} {}>'.format(type(self), self.objectID)

    # def to_json
    #
    # def checksum(self):


class AdminBase(admin.ModelAdmin):
    readonly_fields = ('objectID',)


class Locality(BaseModel):
    class Meta(object):
        verbose_name = _('Locality')
        verbose_name_plural = _('Localities')

    # aka lokalitetskode
    code = models.IntegerField(_('Code'))
    # aka lokalitetsnavn
    name = models.CharField(_('Name'), max_length=255)
    # aka lokalitetstype
    type = models.CharField(_('Type'), max_length=255)

    def __str__(self):
        # i18n: Human-readable description of a Locality
        return _('{0.name} ({0.code})').format(self)


@admin.register(Locality)
class LocalityAdmin(AdminBase):
    list_display = ('code', 'name', 'type')


class Municipality(BaseModel):
    class Meta(object):
        verbose_name = _('Municipality')
        verbose_name_plural = _('Municipalities')

    # aka kommunekode
    code = models.PositiveSmallIntegerField(_('Code'))
    # aka kommunenavn
    name = models.CharField(_('Name'), max_length=255)

    def __str__(self):
        # i18n: Human-readable description of a Municipality
        return _('{0.name}').format(self)


@admin.register(Municipality)
class MunicipalityAdmin(AdminBase):
    list_display = ('name', 'code')


class PostalCode(BaseModel):
    class Meta(object):
        verbose_name = _('Postal Code')
        verbose_name_plural = _('Postal Codes')

    # aka postnummer
    code = models.PositiveSmallIntegerField(_('Number'))
    # aka by
    name = models.CharField(_('City'), max_length=255)

    def __str__(self):
        # i18n: Human-readable description of a PostalCode
        return _('{0.code} {0.name}').format(self)


@admin.register(PostalCode)
class PostalCodeAdmin(AdminBase):
    list_display = ('code', 'name')


class Road(BaseModel):
    class Meta(object):
        verbose_name = _('Road')
        verbose_name_plural = _('Roads')

    # aka vejkode
    code = models.PositiveIntegerField(_('Code'))
    # aka vejnavn
    name = models.CharField(_('Name'), max_length=255)

    # aka forkortetnavn_20_tegn
    shortname = models.CharField(_('Abbreviated Name'), max_length=20)

    # aka dansk_navn
    dkName = models.CharField(_('Danish Name'), max_length=255)
    # aka grønlandsk_navn
    glName = models.CharField(_('Greenlandic Name'), max_length=255, )
    # aka cpr_navn
    cprName = models.CharField(_('CPR Name'), max_length=255)

    def __str__(self):
        # i18n: Human-readable description of a Road
        return _('{0.name} ({0.code})').format(self)


@admin.register(Road)
class RoadAdmin(AdminBase):
    list_display = ('code', 'name', )


class BNumber(BaseModel):
    class Meta(object):
        verbose_name = _('B-Number')
        verbose_name_plural = _('B-Numbers')

    # aka nummer
    number = models.CharField(_('Number'), max_length=255)
    # aka kaldenavn
    name = models.CharField(_('Nickname'), max_length=255)
    # aka blokbetegnelse
    block = models.CharField(_('Block Designation'), max_length=255)

    municipality = models.ForeignKey(Municipality,
                                     verbose_name=_('Municipality'),
                                     null=False, blank=True)

    def __str__(self):
        # i18n: Human-readable description of a BNumber
        return _('{0.name} {0.block} ({0.number})').format(self)


@admin.register(BNumber)
class BNumberAdmin(AdminBase):
    list_display = ('number', 'name', 'block', 'municipality')


class Address(BaseModel):
    class Meta(object):
        verbose_name = _('Address')
        verbose_name_plural = _('Addresses')

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


@admin.register(Address)
class AddressAdmin(AdminBase):
    list_display = ('road', 'houseNumber', 'floor', 'door', 'postalCode',
                    'bNumber')
