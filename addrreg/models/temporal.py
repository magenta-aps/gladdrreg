# -*- mode: python; coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals, print_function

import uuid
import hashlib
import json

from django.core import exceptions, serializers
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from ..util import json_serialize_object


class TemporalModelBase(models.base.ModelBase):
    """
    Meta-class for generating...
    """

    def __new__(cls, name, bases, attrs):
        super_new = super(TemporalModelBase, cls).__new__

        class TemporalModel(*bases):
            class Meta(object):
                abstract = True

            objectID = models.UUIDField(unique=True, db_index=True,
                                        default=uuid.uuid4,
                                        editable=False,
                                        verbose_name=_('Object ID'))
            valid_from = models.DateTimeField(null=True, editable=False)
            valid_to = models.DateTimeField(null=True, editable=False)

            registration_from = models.DateTimeField(db_index=True,
                                                     editable=False)

            def __get_field_dict(self, exclude=None):
                return {
                    field.name: getattr(self, field.name)
                    for field in self._meta.fields
                    if not exclude or field.name not in exclude
                }

            def _maybe_intercept(self):

                '''
                This method does nothing, but exists for tests to override.
                '''
                pass

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

                return super(TemporalModel, self).delete(*args, **kwargs)

            @transaction.atomic(savepoint=False)
            def save(self, *args, **kwargs):
                now = timezone.now()

                if self.registration_from and self.registration_from >= now:
                    raise exceptions.ValidationError(
                        'registration ends before it starts!'
                    )

                self.registration_from = now

                super(TemporalModel, self).save(*args, **kwargs)

                regcls.objects.filter(
                    object=self,
                    registration_to=None,
                ).update(
                    registration_to=now,
                )

                self._maybe_intercept()

                regcls.objects.create(
                    registration_to=None,
                    object=self,
                    **self.__get_field_dict(exclude=('id',))
                )

        regattrs = attrs.copy()
        modelcls = super_new(cls, name, (TemporalModel,), attrs)
        unique_togethers = set(modelcls._meta.unique_together)

        # the registration table contains duplicates of each main table
        # entry, so we have to drop all unique constraints
        # TODO: does this handle many-to-many relations somehow?
        for field in modelcls._meta.fields:
            if not field.unique:
                continue

            # inspired by Field.clone() in Django, but changed by
            # reassigning to unique
            fieldargs, field_kwargs = field.deconstruct()[2:]
            field_kwargs['unique'] = False
            regattrs[field.name] = type(field)(*fieldargs, **field_kwargs)

            if field.name != 'objectID':
                unique_togethers.add((field.name,))

        class RegistrationModel(*bases):
            class Meta(object):
                abstract = True

            object = models.ForeignKey(modelcls, models.SET_NULL, null=True,
                                       related_name='registrations')
            objectID = models.UUIDField(unique=True, db_index=True,
                                        editable=False,
                                        verbose_name=_('Object ID'))

            valid_from = models.DateTimeField(null=True, editable=False)
            valid_to = models.DateTimeField(null=True, editable=False)

            registration_from = models.DateTimeField(db_index=True,
                                                     editable=False)
            registration_to = models.DateTimeField(db_index=True,
                                                   null=True,
                                                   editable=False)

            checksum = models.CharField(db_index=True, null=True,
                                        editable=False, max_length=64)

            def delete(self, *args, **kwargs):
                raise exceptions.PermissionDenied(
                    'Registrations tables are append-only'
                )

            @transaction.atomic(savepoint=False)
            def save(self, *args, **kwargs):
                now = timezone.now()

                if self.registration_from > now:
                    raise exceptions.ValidationError(
                        'registration begins in the future!'
                    )

                elif self.registration_to:
                    if self.registration_to > now:
                        raise exceptions.ValidationError(
                            'registration ends in the future!'
                        )

                    elif self.registration_from <= self.registration_to:
                        raise exceptions.ValidationError(
                            'registration ends before it starts!'
                        )

                self.checksum = self.calculate_checksum()

                super(RegistrationModel, self).save(*args, **kwargs)

            @property
            def fields(self):
                obj = serializers.serialize('python', [self])
                return dict(obj[0]['fields'])

            def calculate_checksum(self):
                input = json.dumps(
                    self.fields,
                    sort_keys=True, default=json_serialize_object,
                    separators=(',', ':')
                ).encode("utf-8")
                digester = hashlib.sha256()
                digester.update(input)
                return digester.hexdigest()

        class Meta(regattrs.get('Meta', object)):
            index_together = [
                ["object", "registration_from", "registration_to", ],
                ["objectID", "registration_from", "registration_to", ],
            ]
            unique_together = [
                constraint + ('objectID',) for constraint in unique_togethers
            ]

            db_table = modelcls._meta.db_table + str('_registrations')

        regattrs['__qualname__'] += 'Registrations'
        regattrs['Meta'] = Meta
        regcls = super_new(cls, name + 'Registrations',
                               (RegistrationModel,), regattrs)
        modelcls.Registrations = regcls

        return modelcls
