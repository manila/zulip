from __future__ import absolute_import

from django.conf import settings

def add_settings(request):
    return {
        'full_navbar':   settings.FULL_NAVBAR,
    }
