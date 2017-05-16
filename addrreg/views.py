from __future__ import absolute_import, unicode_literals, print_function

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views import View
from jsonview.decorators import json_view
from dateutil import parser as dateparser
import pytz

from .models import *
from . import forms


# we really need some views!
class JsonMixin(View):
    @method_decorator(json_view)
    def dispatch(self, request, *args, **kwargs):
        return super(JsonMixin, self).dispatch(request, *args, **kwargs)


class ListChecksumView(JsonMixin):

    all_object_classes = [
        Municipality, District, PostalCode, Locality, BNumber, Road, Address
    ]

    @staticmethod
    def format(item, timestamp=None):
        registrations = item.registrations
        if timestamp is not None:
            registrations = registrations.filter(
                registration_from__gte=timestamp
            )
        return {
            'type': item.get_objecttype_names()[0],
            'objectID': item.objectID,
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
                if object_type_name in cls.get_objecttype_names()
            ]
        else:
            object_classes = ListChecksumView.all_object_classes

        # Get items
        items = []
        for object_class in object_classes:
            qs = object_class.objects
            if timestamp is not None:
                qs = qs.filter(registrations__registration_from__gte=timestamp)

            items.extend(qs.all())

        # Format output
        return {'items': [self.format(item, timestamp) for item in items]}
