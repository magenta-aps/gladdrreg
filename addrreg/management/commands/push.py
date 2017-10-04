import operator

from ...models import *
from ...models.events import *

from jsonview.decorators import _dump_json as dump_json
import grequests
import progress.bar

from django.core.management import base


class Command(base.BaseCommand):
    help = 'Issue a push to the Datafordeler'

    OBJECT_CLASSES = (
        State, Municipality, District, PostalCode, Locality, BNumber,
        Road, Address
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--host', default='http://localhost:8445',
            help=u"Destination server to push to (e.g. https://data.gl)"
        )
        parser.add_argument(
            '--path', default='/odata/gapi/Events',
            help=u"Destination server path to push to"
        )
        parser.add_argument(
            '--full', action='store_true',
            help=u"Do a full synchronisation"
        )
        parser.add_argument(
            '--parallel', type=int, default=1,
            help=u"amount of requests to perform in parallel"
        )
        parser.add_argument(
            '-I', '--include', action='append',
            choices=sorted(cls.type_name() for cls in self.OBJECT_CLASSES),
            help=u"include only the given types"
        )
        parser.add_argument(
            '-X', '--exclude', action='append',
            choices=sorted(cls.type_name() for cls in self.OBJECT_CLASSES),
            help=u"exclude the given types"
        )

    def handle(self, host, path, full, parallel, include, exclude, **kwargs):
        if '://' not in host:
            host = 'https://' + host
            print('Protocol not detected, prepending "https://"')

        endpoint = host + path

        print("Pushing to %s" % endpoint)

        type_map = {
            cls.type_name(): cls
            for cls in self.OBJECT_CLASSES
            if (not include or cls.type_name() in include)
            and (not exclude or cls.type_name() not in exclude)
        }

        session = grequests.Session()

        def post_message(message):
            return grequests.post(
                endpoint,
                data=dump_json(message),
                session=session,
                headers={'Content-Type': 'application/json'},
            )

        def fail(r, exc):
            raise exc

        events = Event.objects.filter(
            updated_type__in=type_map.keys()
        )

        if not full:
            events = events.filter(
                receipt_obtained__isnull=True,
            )

        if not events:
            print('Nothing new.')
            return

        with progress.bar.Bar(max=events.count(),
                              suffix='%(index).0f of %(max).0f - '
                              '%(elapsed_td)s / %(eta_td)s') as bar:

            for r in grequests.imap(
                    map(post_message,
                        map(operator.methodcaller('format'), events)),
                    size=parallel,
                    exception_handler=fail,
            ):
                bar.next()
                r.raise_for_status()
