from ...models import *
from ...models.events import *

from jsonview.decorators import _dump_json as dump_json
import requests

from django.core.management import base

class Command(base.BaseCommand):
    help = 'Issue a push to the Datafordeler'

    def add_arguments(self, parser):
        parser.add_argument(
            '--host', action='store', default='https://localhost',
            help=u"Destination server to push to (e.g. https://data.gl)"
        )
        parser.add_argument(
            '--path', action='store', default='/odata/gapi/Events',
            help=u"Destination server path to push to"
        )

    def handle(self, *args, **kwargs):

        host = kwargs.get('host')
        if '://' not in host:
            host = 'https://' + host
            print('Protocol not detected, prepending "https://"')

        path = kwargs.get('path')

        endpoint = host + path

        print("Pushing to %s" % endpoint)

        all_object_classes = [
            State, Municipality, District, PostalCode, Locality, BNumber,
            Road, Address
        ]
        type_map = {cls.type_name() : cls for cls in all_object_classes}

        qs = Event.objects.filter(
            receipt_obtained__isnull=True,
            updated_type__in=type_map.keys()
        )
        count = qs.count()

        i = 0
        for event in qs:
            cls = type_map[event.updated_type]
            item = cls.Registrations.objects.get(
                checksum=event.updated_registration
            )

            message_body = {
                "beskedVersion": "1.0",
                "eventID": event.eventID,
                "beskedData": {
                    "Objektdata": {
                        "dataskema": cls.__name__,
                        # Using a better serializer, able to serialize
                        # datetimes and uuids
                        "objektdata": dump_json(item.format())
                    },
                }
            }
            r = requests.post(
                endpoint,
                data=dump_json(message_body),
                headers={'Content-Type':'application/json'},
                verify=False
            )
            i += 1
            print("%.1f%%" % (100*i/count), end='\r')
        print("Done! ")