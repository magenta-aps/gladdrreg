# -*- mode: python; coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals, print_function

import uuid

from django.contrib import admin
from django.db import models, transaction
from django.utils.translation import ugettext_lazy as _


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


class AdminBase(admin.ModelAdmin):
    readonly_fields = 'objectID',
