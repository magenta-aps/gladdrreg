# -*- mode: python; coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals, print_function

import uuid

from django.contrib import admin
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


class TemporalModelBase(models.base.ModelBase):
    """
    Meta-class for generating...
    """

    def __init__(cls, name, bases, attrs):
        super(TemporalModelBase, cls).__init__(name, bases, attrs)

        if cls._meta.abstract:
            return

        # copy the attributes so we don't accidentally affect the main model
        attrs = dict(attrs)

        # the registration table contains duplicates of each main table
        # entry, so we have to drop all unique constraints
        # TODO: does this handle many-to-many relations somehow?
        for field in cls._meta.fields:
            if field.unique:
                # inspired by Field.clone() in Django, but changed by
                # reassigning to unique
                fieldargs, field_kwargs = field.deconstruct()[2:]
                field_kwargs['unique'] = False
                attrs[field.name] = type(field)(*fieldargs,
                                                **field_kwargs)

        attrs.update({
            'Meta': type(str('Meta'), (object,), {
                'index_together': [
                    ["object", "registration_from", "registration_to", ],
                    ["objectID", "registration_from", "registration_to", ],
                ],
                'db_table': cls._meta.db_table + str('_registrations'),
            }),
            # required by django
            '__module__': cls.__module__,
            'object': models.ForeignKey(cls, models.SET_NULL, null=True,
                                        related_name='registrations'),
            'registration_to': models.DateTimeField(db_index=True,
                                                    null=True),
        })

        histclass = type(name + str('Registrations'), bases, attrs)
        setattr(cls, 'Registrations', histclass)


class BaseModel(models.Model):
    """
    Abstract BaseModel class specifying a unique object.
    """

    class Meta(object):
        abstract = True

    # aka sumiffiik
    objectID = models.UUIDField(unique=True, db_index=True,
                                default=uuid.uuid4,
                                editable=False,
                                verbose_name=_('Object ID'))
    notes = models.CharField(_('Notes'), blank=True, max_length=255)

    registration_from = models.DateTimeField(editable=False, null=True)

    def __repr__(self):
        return '<{} {}>'.format(type(self), self.objectID)

    def __get_field_dict(self, exclude=None):
        r = {
            field.name: getattr(self, field.name)
            for field in self._meta.fields
            if not exclude or field.name not in exclude
        }
        return r

    def _maybe_intercept(self):
        '''
        This method does nothing, but exists for tests to override.
        '''

    @transaction.atomic(savepoint=False)
    def delete(self, *args, **kwargs):
        if getattr(self, 'Registrations', None):
            now = timezone.now()

            self.Registrations.objects.filter(
                object=self,
                registration_to=None,
            ).update(
                registration_to=now,
            )

        self._maybe_intercept()

        return super(BaseModel, self).delete(*args, **kwargs)

    @transaction.atomic(savepoint=False)
    def save(self, *args, **kwargs):
        if not getattr(self, 'Registrations', None):
            super(BaseModel, self).save(*args, **kwargs)
            return

        now = self.registration_from = timezone.now()

        super(BaseModel, self).save(*args, **kwargs)

        self.Registrations.objects.filter(
            object=self,
            registration_to=None,
        ).update(
            registration_to=now,
        )

        self._maybe_intercept()

        self.Registrations.objects.create(
            registration_to=None,
            object=self,
            **self.__get_field_dict(exclude=('id',))
        )


class AdminBase(admin.ModelAdmin):
    readonly_fields = 'objectID',
