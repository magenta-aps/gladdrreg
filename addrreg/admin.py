# -*- mode: python; coding: utf-8 -*-

from django.contrib import admin

from django.utils.translation import ugettext_lazy as _

from . import apps


# Text to put at the end of each page's <title>.
admin.site.site_title = apps.AddrRegConfig.verbose_name

# Text to put in each page's <h1> (and above login form).
admin.site.site_header = apps.AddrRegConfig.verbose_name

# Text to put at the top of the admin index page.
admin.site.index_title = _('Administration Overview')

# Suppress the "View Site" link, given we have no site!
admin.site.site_url = None
