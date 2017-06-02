# -*- mode: python; coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals, print_function

import functools
import operator
import uuid

from django import forms
from django.contrib import admin
from django.core import validators
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


def _random_sumiffiik():
    return '{{{}}}'.format(uuid.uuid4())


class SumiffiikIDField(models.CharField):
    '''Field for storing a Sumiffiik, which is a UUID wrapped in {}. We
    could use a UUID field, but MS SQL doesn't support those directly,
    so they offer little value.

    '''

    def __init__(self, verbose_name=_('Sumiffiik ID'),
                 max_length=38,
                 default=_random_sumiffiik,
                 db_index=True,
                 null=False, blank=False,
                 **kwargs):

        for k, v in list(locals().items()):
            if k not in ('self', 'kwargs') and k[0] != '_':
                kwargs.setdefault(k, v)

        super().__init__(**kwargs)

    def get_db_prep_value(self, value, *args, **kwargs):
        if value == '[n/a]':
            return None
        else:
            value = '{{{}}}'.format(uuid.UUID(value.strip('{}')))

        return super().get_db_prep_value(value, *args, **kwargs)


class SumiffiikDomainField(models.CharField):

    def __init__(self, verbose_name=_('Sumiffiik Domain'),
                 max_length=64,
                 validators=[validators.URLValidator()],
                 **kwargs):
        for k, v in list(locals().items()):
            if k not in ('self', 'kwargs') and k[0] != '_':
                kwargs.setdefault(k, v)

        super().__init__(**kwargs)

    @property
    def default(self):
        return None

    @default.setter
    def default(self, val):
        pass

    def formfield(self, **kwargs):
        # Passing max_length to forms.CharField means that the value's length
        # will be validated twice. This is considered acceptable since we want
        # the value in the form field (to pass into widget for example).
        defaults = {
            'widget': forms.URLField,
        }
        defaults.update(kwargs)
        return super().formfield(**defaults)


class FormBase(forms.ModelForm):

    class Meta:
        widgets = {
            'note': forms.Textarea(attrs={'cols': 80, 'rows': 4}),
            'last_changed': forms.Textarea(attrs={'cols': 80, 'rows': 4}),
        }

    def clean_sumiffiik(self):
        sumiffiik = str(self.cleaned_data['sumiffiik'])
        try:
            return '{{{}}}'.format(
                uuid.UUID(sumiffiik.strip('{}')),
            )
        except ValueError:
            raise forms.ValidationError(
                _('Enter a valid Sumiffiik, such as {%s}'),
                params=str(uuid.uuid4()),
            )


class AdminBase(admin_extensions.ForeignKeyAutocompleteAdmin):
    form = FormBase

    view_on_site = False

    _fieldsets = (
        (_('State'), {
            'fields': ('state', 'active', 'note'),
            'classes': ('wide',),
        }),
    )

    list_filter = (
        'active',
        'state',
    )

    radio_fields = {
        "state": admin.HORIZONTAL,
    }

    superuser_only = False

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        user = request.user

        if not user.is_superuser and hasattr(self.model, 'municipality'):
            fields += ('municipality',)

        return fields

    def get_related_filter(self, remote_model, request):
        user = request.user
        filters = []

        if getattr(remote_model, 'active', None):
            filters.append(models.Q(active=True))

        if not user.is_superuser:
            if remote_model._meta.label == 'addrreg.Municipality':
                filters.append(models.Q(rights__users=user))

            if hasattr(remote_model, 'municipality'):
                filters.append(models.Q(municipality__rights__users=user))

        return functools.reduce(operator.and_, filters)

    def get_field_queryset(self, db, db_field, request):
        remote_model = db_field.remote_field.model
        queryset = (
            super().get_field_queryset(db, db_field, request) or
            remote_model.objects
        )

        return queryset.filter(self.get_related_filter(remote_model, request))

    def get_search_results(self, request, queryset, search_term):
        user = request.user

        if not user.is_superuser and hasattr(self.model, 'municipality'):
            queryset = queryset.filter(municipality__rights__users=user)

        return super().get_search_results(request, queryset, search_term)

    def __has_municipality(self, request, obj=None):
        if request.user.is_superuser:
            return True
        elif not hasattr(request.user, 'rights'):
            return False
        # can do this in general?

        if not obj:
            return (request.user.rights.all() and
                    hasattr(self.model, 'municipality'))

        elif hasattr(obj, 'municipality'):
            return request.user.rights.filter(
                municipality=obj.municipality
            ).exists()
        else:
            return False

    def save_model(self, request, obj, form, change):
        if (hasattr(type(obj), 'municipality') and
                not hasattr(obj, 'municipality')):
            obj.municipality = request.user.rights.only().get().municipality

        obj._registration_user = request.user

        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return self.__has_municipality(request, obj)

    def has_add_permission(self, request):
        return self.__has_municipality(request)

    def has_module_permission(self, request):
        if self.superuser_only:
            return request.user.is_superuser
        return self.__has_municipality(request)
