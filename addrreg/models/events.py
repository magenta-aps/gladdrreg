# -*- mode: python; coding: utf-8 -*-

import logging
import uuid

from datetime import datetime, timezone

import requests

from django.conf import settings
from django.db import models, transaction

from . import data
from .. import util


class Event(models.Model):
    created = models.DateTimeField(
        db_index=True,
        auto_now=True
    )
    eventID = models.UUIDField()
    objectID = models.UUIDField(db_index=True, null=True)
    updated_registration = models.CharField(max_length=64)
    updated_type = models.CharField(max_length=32)
    receipt_obtained = models.DateTimeField(db_index=True, null=True)
    receipt_errorcode = models.CharField(max_length=64, null=True)

    @transaction.atomic(savepoint=False)
    def save(self, *args, **kwargs):
        if self.eventID is None:
            self.eventID = uuid.uuid4()
        super(Event, self).save(*args, **kwargs)

    @staticmethod
    def create(item, saveItem=True):
        if hasattr(item, 'registrations'):
            for r in item.registrations.all():
                event = Event.create(r)
                transaction.on_commit(event.try_push)

        else:
            item.calculate_checksum(saveItem)
            event = Event(
                objectID=item.objectID,
                updated_type=item.type_name(),
                updated_registration=item.checksum
            )
            event.save()
            transaction.on_commit(event.try_push)

    def receipt(self, errorcode=None):
        self.receipt_obtained = datetime.now(timezone.utc)
        self.receipt_errorcode = errorcode
        self.save()

    def format(self):
        cls = data.ALL_OBJECT_CLASSES[self.updated_type]

        item = cls.Registrations.objects.get(
            checksum=self.updated_registration
        )

        return {
            "beskedVersion": "1.0",
            "eventID": self.eventID,
            "beskedData": {
                "Objektdata": {
                    "dataskema": cls.__name__,
                    # Using a better serializer, able to serialize
                    # datetimes and uuids
                    "objektdata": util.dump_json(item.format())
                },
            }
        }

    def push(self, url):
        return requests.post(
            url,
            data=util.dump_json(self.format()),
            headers={'Content-Type': 'application/json'},
            verify=False
        )

    @property
    def predecessors(self):
        return Event.objects.filter(
            objectID=self.objectID,
            created__lt=self.created,
        ).order_by('created')

    @transaction.atomic(savepoint=False)
    def try_push(self):
        # never push during testing
        if settings.TESTING or not settings.PUSH_URL:
            return

        try:
            for predecessor in self.predecessors.filter(
                    receipt_obtained__isnull=True,
            ):
                predecessor.push(settings.PUSH_URL).raise_for_status()

            self.push(settings.PUSH_URL).raise_for_status()

        except requests.RequestException:
            logging.getLogger('django.request').exception(
                'push notification failed'
            )
