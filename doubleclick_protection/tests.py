# -*- coding: utf-8 -*-

import cPickle
import os

from django.conf import settings
from django.conf.urls.defaults import include, patterns, url
from django.http import HttpResponse, HttpRequest, HttpResponse
from django.test import TestCase
from django.test.client import Client, RequestFactory
from django.views.generic import View

from doubleclick_protection.middleware import (
    CsrfTokenPerRequestMiddleware,
    DoubleClickProtectionMiddleware,)


class MockView(View):
    """Test view for general view tests."""

    def get(self, request):
        return HttpResponse({'a': 1, 'b': 2, 'c': 3})

    def post(self, request):
        return HttpResponse({'a': 1, 'b': 2, 'c': 3})


class MockStaticContentView(View):
    """Test view for static data."""

    def get(self, request):
        response = HttpResponse()
        response['Content-Type'] = ''
        return response


urlpatterns = patterns('',
    url(r'^foo/$', MockView.as_view()),
    url(r'^foo2/$', MockStaticContentView.as_view()),
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
        self.assertIsNotNone(token2)
        self.assertNotEqual(token1, token2)


class DoubleClickProtectionMiddlewareTest(TestCase):
    """Testcase for the :class:`DoubleClickProtectionMiddlewareTest`"""

    urls = 'doubleclick_protection.tests'

    def setUp(self):
        self.OLD_MIDDLEWARE_CLASSES = settings.MIDDLEWARE_CLASSES
        settings.MIDDLEWARE_CLASSES = (
            'django.middleware.csrf.CsrfViewMiddleware',
            'doubleclick_protection.middleware.CsrfTokenPerRequestMiddleware',
            'doubleclick_protection.middleware.DoubleClickProtectionMiddleware')
        self.OLD_DCLICK_CACHE_DIR = settings.DCLICK_CACHE_DIR
        settings.DCLICK_CACHE_DIR = 'test_tokens'

    def tearDown(self):
        settings.MIDDLEWARE_CLASSES = self.OLD_MIDDLEWARE_CLASSES
        settings.DCLICK_CACHE_DIR = self.OLD_DCLICK_CACHE_DIR

    def test_should_create_directories(self):
        self.assertTrue(os.path.isdir('test_tokens'))
        self.assertTrue(os.path.isdir(os.path.join('test_tokens', 'tokens')))
        self.assertTrue(os.path.isdir(os.path.join('test_tokens',
                                                   'delivered_tokens')))
        self.assertTrue(os.path.isdir(os.path.join('test_tokens',
                                                   'file_infos')))
        self.assertTrue(os.path.isdir(os.path.join('test_tokens',
                                                   'received_tokens')))

    def test_should_add_delivered_token(self):
        # Middlewares need to be called manually to be able to fetch the
        # generated token.
        m1 = CsrfTokenPerRequestMiddleware()
        m2 = DoubleClickProtectionMiddleware()
        factory = RequestFactory()
        request = factory.get('foo/')
        request.session = {}
        response = HttpResponse()
        m1.process_view(request, lambda x: x, [], {})
        m2.process_request(request)
        m2.process_response(request, response)
        token = request.META.get('CSRF_COOKIE', None)
        self.assertTrue(os.path.isfile(os.path.join('test_tokens',
            'delivered_tokens', token)))
        self.assertTrue(os.path.isfile(os.path.join('test_tokens',
            'tokens', token)))
        self.assertTrue(os.path.isfile(os.path.join('test_tokens',
            'file_infos', token)))

    def test_should_save_response(self):
        m1 = CsrfTokenPerRequestMiddleware()
        m2 = DoubleClickProtectionMiddleware()
        factory = RequestFactory()
        request = factory.get('foo/')
        request.session = {}
        response = HttpResponse()
        m1.process_view(request, lambda x: x, [], {})
        m2.process_request(request)
        m2.process_response(request, response)
        token = request.META.get('CSRF_COOKIE', None)
        fp = open(os.path.join('test_tokens', 'tokens', token), 'rb')
        data = cPickle.load(fp)
        fp.close()
        self.assertEqual(data, ['', 200,
                        'Content-Type: text/html; charset=utf-8'])
        fp = open(os.path.join('test_tokens', 'file_infos', token), 'rb')
        data = cPickle.load(fp)
        fp.close()
        self.assertEqual(data, True)

    def test_should_skip_on_wrong_content_type(self):
        pass

    def test_should_add_received_token(self):
        pass

    def test_should_fail_on_wrong_token(self):
        pass

    def test_should_return_response_from_file(self):
        pass


