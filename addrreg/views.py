from __future__ import absolute_import, unicode_literals, print_function

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.utils.translation import ugettext as _

from . import forms, utils


@login_required(login_url='/admin/login')
def upload_file(request):
    if request.method == 'POST':
        form = forms.FileForm(request.POST, request.FILES)
        if form.is_valid():
            utils.import_spreadsheet(request.FILES['file'])
            return HttpResponse(_('Spreadsheet successfully imported!'),
                                content_type='text/plain')
        else:
            return HttpResponseBadRequest("Missing file! " +
                                          ', '.join(request.FILES))

    return render(request, 'upload.html')
