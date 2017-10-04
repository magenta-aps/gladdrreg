# -*- mode: python; coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals, print_function

import uuid
import hashlib
import json

from django.conf import settings
from django.core import exceptions, serializers
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from .events import Event
from ..util import json_serialize_object


class TemporalModelBase(models.base.ModelBase):
    """
    Meta-class for generating...
    """

    def __new__(cls, name, bases, attrs):
        super_new = super().__new__

        class TemporalModel(*bases):
            class Meta(object):
                abstract = True

            objectID = models.UUIDField(unique=True, db_index=True,
                                        default=uuid.uuid4,
                                        editable=False,
                                        verbose_name=_('Object ID'))
            valid_from = models.DateTimeField(null=True, editable=False,
                                              verbose_name=_('Valid From'))
            valid_to = models.DateTimeField(null=True, editable=False,
                                            verbose_name=_('Valid To'))

            registration_from = models.DateTimeField(
                db_index=True,
                editable=False,
                verbose_name=_('Registration Time'),
            )

            @property
            def registrations(self):
                return self.Registrations.objects.filter(object=self)

            @property
            def created(self):
                self.registrations.aggregate(models.Min('registration_from'))

            @property
            def last_changed(self):
                return self.registration_from

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

                return super().delete(*args, **kwargs)

            @transaction.atomic(savepoint=False)
            def save(self, *args, **kwargs):
                now = timezone.now()

                try:
                    user = self._registration_user
                    del self._registration_user
                except AttributeError:
                    user = None

                if self.registration_from and self.registration_from >= now:
                    raise exceptions.ValidationError(
                        'registration ends before it starts!'
                    )

                self.registration_from = now

                super().save(*args, **kwargs)

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
                    registration_user=user,
                    **self.__get_field_dict(exclude=('id',))
                )

            def format(self, timestamp=None):
                registrations = self.registrations
                if timestamp is not None:
                    registrations = registrations.filter(
                        registration_from__gte=timestamp
                    )
                for registration in registrations.all():
                    registration.calculate_checksum()
                return {
                    'type': self.type_name(),
                    'objectID': self.objectID,
                    'registreringer': [
                        {
                            'sekvensNummer': index,
                            'checksum': registration.checksum
                        } for index, registration in
                        enumerate(
                            registrations.order_by('registration_from')
                        )
                    ]
                }

            def natural_key(self):
                return {
                    'uuid': self.objectID,
                    'domaene': "https://data.gl/gladdreg/%s/1/rest/" %
                               self.type_name()
                }

        regattrs = attrs.copy()
        modelcls = super_new(cls, name, (TemporalModel,), attrs)

        # the registration table contains duplicates of each main table
        # entry, so we have to drop all unique constraints
        # TODO: does this handle many-to-many relations somehow?
        for field in modelcls._meta.fields:
            # inspired by Field.clone() in Django, but changed by
            # reassigning to unique, and supressing swappable so we
            # retain self-references as strings
            _swappable = getattr(field, 'swappable', None)

            if _swappable:
                field.swappable = False

            fieldargs, field_kwargs = field.deconstruct()[2:]

            if _swappable is not None:
                field.swappable = _swappable

            if not field.unique and not field_kwargs.get('unique'):
                continue

            field_kwargs['unique'] = False
            field_kwargs['db_index'] = True

            regattrs[field.name] = type(field)(*fieldargs, **field_kwargs)

        class RegistrationModel(*bases):
            class Meta(object):
                abstract = True

            object = models.ForeignKey(modelcls, models.SET_NULL, null=True,
                                       related_name='registrations',
                                       verbose_name=_('Object'))
            objectID = models.UUIDField(unique=True, db_index=True,
                                        editable=False,
                                        verbose_name=_('Object ID'))

            valid_from = models.DateTimeField(null=True, editable=False,
                                              verbose_name=_('Valid From'))
            valid_to = models.DateTimeField(null=True, editable=False,
                                            verbose_name=_('Valid To'))

            registration_user = models.ForeignKey(
                settings.AUTH_USER_MODEL, models.PROTECT,
                null=True,
                db_index=True,
                verbose_name=_('Actor'),
            )
            registration_from = models.DateTimeField(
                db_index=True,
                editable=False,
                verbose_name=_('Registration From'),
            )
            registration_to = models.DateTimeField(
                db_index=True,
                null=True,
                editable=False,
                verbose_name=_('Registration From'),
            )

            checksum = models.CharField(db_index=True, null=True,
                                        editable=False, max_length=64,
                                        verbose_name=_('Checksum'))

            modelclass = modelcls

            @classmethod
            def type_name(cls):
                return cls.modelclass.type_name()

            def delete(self, *args, **kwargs):
                raise exceptions.PermissionDenied(
                    'Registrations tables are append-only'
                )

            @transaction.atomic(savepoint=False)
            def save(self, *args, **kwargs):

                if self.pk is None:
                    Event.create(self, False)

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

                super().save(*args, **kwargs)

            @property
            def fields(self):
                obj = serializers.serialize('python_with_identity', [self])
                return dict(obj[0]['fields'])

            def calculate_checksum(self, save=True):
                if self.checksum is None:
                    input = json.dumps(
                        self.fields,
                        sort_keys=True, default=json_serialize_object,
                        separators=(',', ':')
                    ).encode("utf-8")
                    digester = hashlib.sha256()
                    digester.update(input)
                    self.checksum = digester.hexdigest()
                    if save:
                        self.save()

            def format(self):
                fields = self.fields
                for exclusion in [
                    'registration_from', 'registration_to', 'valid_from',
                    'valid_to', 'checksum', 'object', 'objectID',
                    'registration_user',
                ]:
                    fields.pop(exclusion)

                # we need a string rather than the foreign key object
                if self.registration_user:
                    fields['registration_user'] = \
                        self.registration_user.username

                return {
                    'checksum': self.checksum,
                    'registreringFra': self.registration_from,
                    'registreringTil': self.registration_to,
                    'entity': {
                        'uuid': self.objectID,
                        'domaene': 'https://data.gl/gladdreg/' +
                                   self.type_name() + "/1/rest/"
                    },
                    'virkninger': [{
                        'virkningFra': (self.valid_from or
                                        self.registration_from),
                        'virkningTil': self.valid_to or self.registration_to,
                        'data': [
                            fields
                        ]
                    }]
                }

        class Meta(regattrs.get('Meta', object)):
            index_together = [
                ["object", "registration_from", "registration_to", ],
                ["objectID", "registration_from", "registration_to", ],
            ]

            db_table = modelcls._meta.db_table + str('_registrations')

            verbose_name = _('{} Registration').format(
                modelcls._meta.verbose_name
            )
            verbose_name_plural = _('{} Registrations').format(
                modelcls._meta.verbose_name
            )

        regattrs['__qualname__'] += 'Registrations'
        regattrs['Meta'] = Meta
        regcls = super_new(cls, name + 'Registrations',
                           (RegistrationModel,), regattrs)
        modelcls.Registrations = regcls

        return modelcls
