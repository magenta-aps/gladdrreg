from __future__ import absolute_import, unicode_literals, print_function

from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, render_to_response
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from jsonview.decorators import json_view
from dateutil import parser as dateparser
import pytz
import json

from .models import *
from . import forms


class JsonView(View):

    @method_decorator(json_view)
    def dispatch(self, request, *args, **kwargs):
        return super(JsonView, self).dispatch(request, *args, **kwargs)


class GetNewEventsView(JsonView):

    @staticmethod
    def format(event):
        return {
            'eventID': event.eventID,
            'beskedVersion': 1,
            'beskedData': {
                'Objektreference': {
                    'objektreference': "http://localhost:8000" + reverse(
                        'getRegistrations', args=[
                            event.updated_type.lower(),
                            event.updated_registration,
                        ]
                    )
                }
            }
        }

    def get(self, request, *args, **kwargs):
        new_events = events.Event.objects.filter(
            receipt_obtained__isnull=True,
        )
        data = {
            'events': [self.format(event) for event in new_events.all()]
        }
        return data


@method_decorator(csrf_exempt, name='dispatch')
class Receipt(View):

    def post(self, request, eventID, *args, **kwargs):
        print(request.body.decode('utf-8'))
        receipt = json.loads(request.body.decode('utf-8'))
        try:
            event = events.Event.objects.get(eventID=eventID)
        except events.Event.DoesNotExist:
            return HttpResponse(status=404)
        status = receipt.get('status')
        if status == 'ok':
            event.receipt()
        elif status == 'failed':
            event.receipt(receipt.get('errorCode'))
        return HttpResponse(status=201)


class ListChecksumView(JsonView):

    all_object_classes = [
        Municipality, District, PostalCode, Locality, BNumber, Road, Address
    ]

    def get(self, request, *args, **kwargs):

        if 'timestamp' in request.GET:
            # Parse the timestamp parameter
            timestamp = dateparser.parse(
                request.GET.get('timestamp'),
                dayfirst=True, yearfirst=False
            )
            # UTC if no zone is set
            if timestamp.tzinfo is None:
                timestamp = pytz.utc.localize(timestamp)
        else:
            timestamp = None

        if 'objectType' in request.GET:
            # Get objectType, default to all
            object_type_name = request.GET['objectType'].lower()
            object_classes = [
                cls
                for cls in ListChecksumView.all_object_classes
                if object_type_name in cls.type_names()
            ]
        else:
            object_classes = ListChecksumView.all_object_classes

        # Get items
        entities = []
        for object_class in object_classes:
            qs = object_class.objects
            if timestamp is not None:
                qs = qs.filter(registrations__registration_from__gte=timestamp)

            entities.extend(qs.all())

        # Format output
        return {'items': [entity.format(timestamp) for entity in entities]}


class GetRegistrationsView(JsonView):

    all_object_classes = {
        cls.type_name(): cls
        for cls in [
            State, Municipality, District, PostalCode, Locality, BNumber, Road,
            Address
        ]
    }

    def get(self, request, type, checksums, *args, **kwargs):
        items = {}
        object_class = self.all_object_classes[type]
        for checksum in checksums.split(';'):
            registration = None
            try:
                registration = object_class.Registrations.objects.get(
                    checksum=checksum
                )
                items[checksum] = registration.format()
            except object_class.Registrations.DoesNotExist:
                pass

        print(items)
        return items


def access_denied_handler(request):
    response = render_to_response(
        'access_denied.html',
        dict(
            admin.site.each_context(request),
            path=request.path,
            delay=15,
        ),
    )
    response.status_code = 403

    return response
