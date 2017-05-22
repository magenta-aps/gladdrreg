# -*- mode: python; coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals, print_function

import uuid

from django import forms
from django.contrib import admin
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django_extensions import admin as admin_extensions


class ForeignKey(models.ForeignKey):
    '''Customised ForeignKey subclass with our defaults'''

    def __init__(self, to, verbose_name, **kwargs):
        kwargs.setdefault('on_delete', models.PROTECT)
        kwargs.setdefault('db_index', True)
        kwargs.setdefault('limit_choices_to', {'active': True})

        super().__init__(to=to, verbose_name=verbose_name, **kwargs)


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

    @classmethod
    def type_name(cls):
        return cls.__name__.lower()

    @classmethod
    def alias_names(cls):
        return []

    @classmethod
    def type_names(cls):
        return [cls.type_name()] + cls.alias_names()


class SumiffiikIDField(models.UUIDField):
    def __init__(self, **kwargs):
        kwargs.setdefault('verbose_name', _('Sumiffiik ID'))
        kwargs.setdefault('default', uuid.uuid4)
        kwargs.setdefault('db_index', True)

        kwargs.setdefault('null', False)
        kwargs.setdefault('blank', False)

        # MS-SQL considers null values similar :(
        kwargs.setdefault('unique', not kwargs['null'])

        super().__init__(**kwargs)

    def get_db_prep_value(self, value, *args, **kwargs):
        if not isinstance(value, str):
            pass
        elif value.startswith('{') and value.endswith('}'):
            value = value[1:-1]
        elif value == '[n/a]':
            return None

        return super().get_db_prep_value(value, *args, **kwargs)


class SumiffiikDomainField(models.CharField):
    def __init__(self, **kwargs):
        kwargs.setdefault('verbose_name', _('Sumiffiik Domain'))
        kwargs.setdefault('max_length', 64)

        super().__init__(**kwargs)

    @property
    def default(self):
        return None

    @default.setter
    def default(self, val):
        pass


class AdminBase(admin_extensions.ForeignKeyAutocompleteAdmin):
    class Meta:
        widgets = {
            'note': forms.Textarea(attrs={'cols': 80, 'rows': 4}),
            'last_changed': forms.Textarea(attrs={'cols': 80, 'rows': 4}),
        }

    view_on_site = False

    list_filter = (
        'active',
        'state',
    )

    radio_fields = {
        "state": admin.HORIZONTAL,
    }

