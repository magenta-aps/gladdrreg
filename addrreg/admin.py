# -*- mode: python; coding: utf-8 -*-

from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.contrib.auth import models as auth_models

from django.utils.translation import ugettext_lazy as _

from . import apps
from . import forms


# Restrict available filters only to things that exist.
admin.FieldListFilter.register(
    lambda f: f.remote_field,
    admin.RelatedOnlyFieldListFilter,
    take_priority=True,
)

# Text to put at the end of each page's <title>.
admin.site.site_title = apps.AddrRegConfig.verbose_name

# Text to put in each page's <h1> (and above login form).
admin.site.site_header = apps.AddrRegConfig.verbose_name

# Text to put at the top of the admin index page.
admin.site.index_title = _('Administration Overview')

# Link to documentation
admin.site.site_url = apps.AddrRegConfig.documentation


class UserAdmin(auth_admin.UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {'fields': (
            'is_active', 'is_staff', 'is_superuser',
        )}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2',
                       'is_staff', 'is_superuser'),
        }),
    )


admin.site.unregister(auth_models.User)
admin.site.register(auth_models.User, UserAdmin)
