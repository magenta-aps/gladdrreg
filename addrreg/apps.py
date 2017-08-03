from __future__ import absolute_import, unicode_literals, print_function

from django.apps import AppConfig

from django.utils.translation import ugettext_lazy as _


class AddrRegConfig(AppConfig):
    name = 'addrreg'
    verbose_name = _('Greenlandic Address Reference Register')
    documentation = 'https://redmine.magenta-aps.dk/projects/dafodoc/wiki/2_Adresseopslagsregistret'