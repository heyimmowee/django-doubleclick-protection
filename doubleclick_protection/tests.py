# -*- coding: utf-8 -*-

from django.conf.urls.defaults import include, patterns, url
from django.http import HttpResponse, HttpRequest
from django.test import TestCase
from django.test.client import Client, RequestFactory
from django.views.generic import View

from .middleware import CsrfTokenPerRequestMiddleware


class MockView(View):

    def get(self, request):
        return HttpResponse({'a': 1, 'b': 2, 'c': 3})

    def post(self, request):
        return HttpResponse({'a': 1, 'b': 2, 'c': 3})


urlpatterns = patterns('',
    url(r'^foo/$', MockView.as_view()),
)


class CsrfTokenPerRequestMiddlewareTest(TestCase):
    """Testcase for the :class:`CsrfTokenPerRequestMiddleware`"""

    def setUp(self):
        self.middleware = CsrfTokenPerRequestMiddleware()

    def test_should_generate_new_token_per_request(self):
        factory = RequestFactory()
        request = factory.get('foo/')
        request.session = {}
        response = self.middleware.process_view(request, lambda x: x, [], {})
        token1 = request.META.get('CSRF_COOKIE', None)
        self.assertIsNotNone(token1)
        request = factory.get('foo/')
        request.session = {}
        response = self.middleware.process_view(request, lambda x: x, [], {})
        token2 = request.META.get('CSRF_COOKIE', None)
        self.assertNotEqual(token1, token2)
