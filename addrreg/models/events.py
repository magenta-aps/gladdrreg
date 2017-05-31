# -*- mode: python; coding: utf-8 -*-

import uuid
from datetime import datetime, timezone

from django.db import models, transaction

class Event(models.Model):
    created = models.DateTimeField(
        auto_now=True
    )
    eventID = models.UUIDField()
    updated_registration = models.CharField(max_length=64)
    updated_type = models.CharField(max_length=32)
    receipt_obtained = models.DateTimeField(null=True)
    receipt_errorcode = models.CharField(max_length=32, null=True)

    @transaction.atomic(savepoint=False)
    def save(self, *args, **kwargs):
        if self.eventID is None:
            self.eventID = uuid.uuid4()
        super(Event, self).save(*args, **kwargs)

    @staticmethod
    def create(item):
        if hasattr(item, 'registrations'):
            for r in item.registrations.all():
                Event.create(r)
        else:
            item.calculate_checksum()
            print(item.type_name()+"    "+item.checksum)
            event = Event(
                updated_type=item.type_name(),
                updated_registration=item.checksum
            )
            event.save()

    def receipt(self, errorcode=None):
        self.receipt_obtained = datetime.now(timezone.utc)
        self.receipt_errorcode = errorcode
        self.save()
