# -*- mode: python; coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals, print_function

from django.contrib import admin
from django.db import models
from django.utils.translation import ugettext_lazy as _


class AbstractModel(models.Model):
    """
    Abstract BaseModel class specifying a unique object.
    """

    class Meta(object):
        abstract = True

    state = models.ForeignKey('addrreg.State', models.PROTECT,
                              verbose_name=_('State'), db_index=True,
                              related_name='+')
    active = models.BooleanField(_('Active'), default=True)
    note = models.CharField(_('Notes'), null=True, max_length=255)


class AbstractSumiffiikModel(AbstractModel):
    class Meta(object):
        abstract = True

    sumiffiik = models.CharField(_('Sumiffiik'), max_length=38, unique=True,
                                 null=True, db_index=True)


class AdminBase(admin.ModelAdmin):
    view_on_site = False

    radio_fields = {
        "state": admin.HORIZONTAL,
    }

    list_filter = (
        'active',
        'state',
    )
