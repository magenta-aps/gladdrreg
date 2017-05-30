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


class SumiffiikIDField(models.UUIDField):
    def __init__(self, **kwargs):
        kwargs.setdefault('verbose_name', _('Sumiffiik ID'))
        kwargs.setdefault('default', uuid.uuid4)
        kwargs.setdefault('db_index', True)

        kwargs.setdefault('null', False)
        kwargs.setdefault('blank', False)

        super().__init__(**kwargs)

    def get_db_prep_value(self, value, *args, **kwargs):
        if not isinstance(value, str):
            pass
        elif value.startswith('{') and value.endswith('}'):
            value = value[1:-1]
        elif value == '[n/a]':
            return None

        return super().get_db_prep_value(value, *args, **kwargs)

    def formfield(self, **kwargs):
        # Passing max_length to forms.CharField means that the value's length
        # will be validated twice. This is considered acceptable since we want
        # the value in the form field (to pass into widget for example).
        defaults = {
            'widget': SumiffiikIDInput(attrs={'maxlength': 38})
        }
        defaults.update(kwargs)
        return super().formfield(**defaults)


class SumiffiikIDInput(admin.widgets.AdminTextInputWidget):
    def render(self, name, value, attrs=None):
        if value is not None:
            value = '{{{}}}'.format(uuid.UUID(value.strip('{}')))

        return super().render(name, value, attrs)


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

class FormBase(forms.ModelForm):
    class Meta:
        widgets = {
            'note': forms.Textarea(attrs={'cols': 80, 'rows': 4}),
            'last_changed': forms.Textarea(attrs={'cols': 80, 'rows': 4}),
        }

    def clean_sumiffiik(self):
        sumiffiik = self.cleaned_data['sumiffiik']
        try:
            return uuid.UUID(sumiffiik.strip('{}'))
        except ValueError:
            raise ValidationError



class AdminBase(admin_extensions.ForeignKeyAutocompleteAdmin):
    form = FormBase

    view_on_site = False

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

        if not request.user.is_superuser and hasattr(self.model, 'municipality'):
            fields += ('municipality',)

        return fields

    def get_field_queryset(self, db, db_field, request):
        queryset = super().get_field_queryset(db, db_field, request)
        user = request.user

        # should work when a queryset is returned, but untested
        if queryset is None:
            queryset = db_field.remote_field.model.objects

        if getattr(db_field.remote_field.model, 'active', None):
            queryset = queryset.filter(active=True)

        if not user.is_superuser:
            if db_field.remote_field.model._meta.label == 'addrreg.Municipality':
                queryset = queryset.filter(rights__users=user)

            if hasattr(db_field.remote_field.model, 'municipality'):
                queryset = queryset.filter(municipality__rights__users=user)

        return queryset

    def get_search_results(self, request, queryset, search_term):
        if not request.user.is_superuser and hasattr(self.model, 'municipality'):
            queryset = queryset.filter(municipality__rights__users=request.user)

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
