from __future__ import absolute_import, unicode_literals, print_function

import openpyxl
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.utils.translation import ugettext as _

from . import forms, models


def _read_spreadsheet(fp):
    wb = openpyxl.load_workbook(fp, read_only=True, data_only=True)
    rows = wb.active.rows

    column_names = {
        cellidx: cell.value for cellidx, cell in
        enumerate(next(rows))
    }

    for row in rows:
        r = {
            column_names[cellidx]: cell.value
            for cellidx, cell in enumerate(row)
        }
        if any(r.values()):
            yield r


def _get_locality(vals):
    code = vals['LOKALITETSNR']
    if not code or not code.strip():
        return None

    obj, created = models.Locality.objects.get_or_create(
        code=code,
        defaults={
            'name': vals['LOKALITETSNAVN'].rstrip(),
            'type': {
                'By': models.LocalityType.TOWN,
                'Bygd': models.LocalityType.VILLAGE,
                'Station': models.LocalityType.STATION,
                'Lufthavn': models.LocalityType.AIRPORT,
                'Ukendt': models.LocalityType.UNKNOWN,
            }[vals['LOKALITETS_TYPE_NAVN'].rstrip()],
        }
    )

    return obj


def _get_municipality(vals):
    obj, created = models.Municipality.objects.get_or_create(
        code=vals['KOMMUNEKODE'],
        defaults={
            'name': vals['KOMNAVN'].rstrip(),
        }
    )

    return obj


def _get_postalcode(vals):
    obj, created = models.PostalCode.objects.get_or_create(
        code=int(vals['POSTNR']),
        defaults={
            'name': vals['POSTDISTRIKT'].rstrip(),
        }
    )

    return obj


def _get_road(vals):
    obj, created = models.Road.objects.get_or_create(
        code=vals['VEJKODE'],
        defaults={
            'name': vals['VEJNAVN'].rstrip(),
        }
    )

    return obj


def _get_bnumber(vals):
    obj, created = models.BNumber.objects.get_or_create(
        number=vals['BNR'],
        municipality=_get_municipality(vals),
    )

    return obj


def import_spreadsheet(fp):
    for vals in _read_spreadsheet(fp):
        models.Address.objects.create(
            houseNumber=vals['HUSNR'] or '',
            floor=vals['ETAGE'] or '',
            door=vals['SIDE'] or '',
            locality=_get_locality(vals),
            bNumber=_get_bnumber(vals),
            road=_get_road(vals),
            postalCode=_get_postalcode(vals)
        )


@login_required(login_url='/admin/login')
def upload_file(request):
    if request.method == 'POST':
        form = forms.FileForm(request.POST, request.FILES)
        if form.is_valid():
            models.import_spreadsheet(request.FILES['file'])
            return HttpResponse(_('Spreadsheet successfully imported!'),
                                content_type='text/plain')
        else:
            return HttpResponseBadRequest("Missing file! " +
                                          ', '.join(request.FILES))

    return render(request, 'upload.html')
