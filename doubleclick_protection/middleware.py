# -*- coding: utf-8 -*-

"""Middleware class."""

from django.middleware.csrf import get_token

HTML_CONTENT_TYPES = (
    'text/html',
    'application/xhtml+xml',)


class DoubleClickProtectionMiddleware(object):

    def process_request(self, request):
        # Check for request.user.is_anonymous() ?
        # Check for content-type?
        if request.method != 'POST':
            return
        token = request.POST.get('csrfmiddlewaretoken', None)

    #def process_response(self, request, response):
    #    pass
