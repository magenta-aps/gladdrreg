from __future__ import absolute_import, unicode_literals, print_function

from django import views
from django.urls import reverse
from django.utils.translation import ugettext as _
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.translation import to_locale, get_language


def placeholder(request):
    return HttpResponse(_("Move along, nothing to see here."))
