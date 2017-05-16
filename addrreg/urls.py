"""addrsite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""

from __future__ import absolute_import, unicode_literals, print_function

from django.views.generic import RedirectView

from django.conf.urls import url, include
from django.contrib import admin

from . import views

urlpatterns = [
    url(r'^admin/', include(admin.site.urls), name='admin'),
    url(r'^$', RedirectView.as_view(url='/admin/'), name='redirect_admin'),
    url(r'^getNewEvents/?$', views.GetNewEventsView.as_view()),
    url(r'^receipt/?$', views.Receipt.as_view()),
    url(r'^listChecksums/?$', views.ListChecksumView.as_view()),
    url(r'^get/(?P<checksums>[0-9a-f;]+)$',
        views.GetRegistrationsView.as_view())
]
