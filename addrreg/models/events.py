# -*- mode: python; coding: utf-8 -*-

import uuid
from datetime import datetime

from django.db import models, transaction

class Event(models.Model):
    created = models.DateTimeField(
        auto_now=True
    )
    eventID = models.UUIDField()
    updated_registration = models.CharField(max_length=64)
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
            event = Event(updated_registration=item.checksum)
            event.save()

    def receipt(self, errorcode=None):
        self.receipt_obtained = datetime.utcnow()
        self.receipt_errorcode = errorcode
        self.save()
