
from ...models import *
from ...models.events import *

from jsonview.decorators import _dump_json as dump_json
import requests

from django.core.management import base

class Command(base.BaseCommand):
    help = 'Issue a push to the Datafordeler'

    def handle(self, *args, **kwargs):
        endpoint = "http://localhost:8444/odata/gapi/Events"

        for event in Event.objects.filter(
            receipt_obtained__isnull=True,
            updated_type='municipality'
        ):
            item = Municipality.Registrations.objects.get(
                checksum=event.updated_registration)

            message_body = {
                "beskedVersion": "1.0",
                "eventID": event.eventID,
                "beskedData": {
                    "Objektdata": {
                        "dataskema": "Municipality",
                        # Using a better serializer, able to serialize
                        # datetimes and uuids
                        "objektdata": dump_json(item.format())
                    }
                }
            }
            requests.post(
                endpoint,
                data=dump_json(message_body),
                headers={'Content-Type':'application/json'}
            )

