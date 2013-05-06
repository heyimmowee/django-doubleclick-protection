# -*- coding: utf-8 -*-

# TODO(hk): Skip on requests with static data

"""Middleware class."""

import cPickle
import logging
import os
import thread
import threading
import time

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.middleware.csrf import get_token, _get_new_csrf_key


logger = logging.getLogger(__name__)


cache_dir_lock = threading.RLock()
before_main_lock = threading.RLock()


HTML_CONTENT_TYPES = (
    'text/html',
    'application/xhtml+xml',)

MAX_WAIT = 5 # 30


class CsrfTokenPerRequestMiddleware(object):
    """Middleware to generate a new CSRF token per request."""

    def process_view(self, request, callback, callback_args, callback_kwargs):
        # Overwrite Django's token. We want a new token per request.
        #import ipdb; ipdb.set_trace()
        token = _get_new_csrf_key()
        print 'Generated token:', token
        request.META['CSRF_COOKIE'] = token


class DoubleClickProtectionMiddleware(object):
    """Middleware to prevent multiple POST events with the same token."""

    def __init__(self):
        """Constructor"""
        self._cache_dir = settings.DCLICK_CACHE_DIR
        self._create_directories()

    def _create_directories(self):
        """Creates all necessary directories to store tokens."""
        dirs = (self._cache_dir,
                os.path.join(self._cache_dir, 'tokens'),
                os.path.join(self._cache_dir, 'delivered_tokens'),
                os.path.join(self._cache_dir, 'file_infos'),
                os.path.join(self._cache_dir, 'received_tokens'))
        for dir in dirs:
            cache_dir_lock.acquire()
            try:
                if os.path.isdir(dir):
                    continue
                try:
                    os.makedirs(dir)
                except OSError, err:
                    raise StandardError(
                        'Could\'nt create directory %s: %s'
                        % (dir, str(err)))
            finally:
                cache_dir_lock.release()

    def _file_was_created(self, token):
        if self.token_exists('received_tokens', token):
            fname = os.path.join(self._cache_dir, 'file_infos', token)
            fp = open(fname, 'rb')
            data = cPickle.load(fp)
            fp.close()
            return bool(data)
        return False

    def _file_was_saved(self, token):
        fname = os.path.join(self._cache_dir, 'file_infos', token)
        fp = open(fname, 'rb')
        data = cPickle.load(fp)
        fp.close()
        return data == True

    def _token_was_delivered(self, token):
        return self.token_exists('delivered_tokens', token)

    def add_delivered_token(self, token):
        fname = os.path.join(self._cache_dir, 'tokens', token)
        if os.path.isfile(fname):
            return False
        if not self.token_exists('delivered_tokens', token):
            fname = os.path.join(self._cache_dir, 'delivered_tokens', token)
            try:
                open(fname, 'w').close()
            except OSError, err:
                raise StandardError(
                    ('Could\'nt write delivered token %s') % str(err))
            return True
        return False

    def add_received_token(self, token):
        fname = os.path.join(self._cache_dir, 'received_tokens', token)
        try:
            open(fname, 'w').close()
        except OSError, err:
            raise StandardError(
                'Error writing the information of a received token: %s'
                % str(err))

    def token_exists(self, dir, token):
        """Checks, whether the token exists as a file.

        :param dir:
        :param token:
        """
        try:
            os.stat(os.path.join(self._cache_dir, dir, token))
        except OSError:
            return False
        return True

    def remove_token(self, dir, token):
        """Removes a token from a directory.

        :param dir:
        :param token:
        """
        fname = os.path.join(self._cache_dir, dir, token)
        try:
            os.remove(fname)
        except OSError, err:
            raise StandardError('Could\'nt remove token %s in directory %s: %s'
                % (token, dir, str(err)))

    def serialize_headers(self, response):
        """HTTP headers as a bytestring."""
        headers = [
            ('%s: %s' % (key, value)).encode('us-ascii')
            for key, value in response._headers.values()
        ]
        return b'\r\n'.join(headers)

    def process_request(self, request):
        # Check for request.user.is_anonymous() ?
        # Check for content-type?
        if request.method != 'POST':
            return None
        token = request.POST.get('csrfmiddlewaretoken', None)
        if token is None:
            return None
        print 'Got token:', token
        if not self._token_was_delivered(token):
            return HttpResponseForbidden('Received unknown token')
        before_main_lock.acquire()
        try:
            #import ipdb; ipdb.set_trace()
            if self.token_exists('received_tokens', token):
                #import ipdb; ipdb.set_trace()
                starting_time = time.time()
                #while not self._file_was_saved(token):
                 #   delta = time.time() - starting_time
                 #   if delta > MAX_WAIT:
                 #       #logger.warning(
                 #       #    'Thread %s had to wait more than %s seconds.'
                 #       #    % (thread.get_ident(), MAX_WAIT))
                 #       print 'Thread %s had to wait more than %s seconds.' % (thread.get_ident(), MAX_WAIT)
                 #       return
                 #   threading._sleep(1)
                fname = os.path.join(self._cache_dir, 'tokens', token)
                if os.path.isfile(fname):
                    print 'Returning old response'
                    fp = open(fname, 'rb')
                    data = cPickle.load(fp)
                    fp.close()
                    return HttpResponse(content=data[0], status=data[1])
                else:
                    print 'Response not found'
                    # log warning
                    return None
            else:
                print "Add received token:", token
                fname = os.path.join(self._cache_dir, 'file_infos', token)
                fp = open(fname, 'w')
                cPickle.dump(False, fp)
                fp.close()
                self.add_received_token(token)
        finally:
            before_main_lock.release()
        return None

    def process_response(self, request, response):
        #if request.method != 'GET':
        #    return response
        #token = request.COOKIES.get('csrftoken')
        token = request.META.get('CSRF_COOKIE')
        if token is None:
            return response
        if not self.token_exists('delivered_tokens', token):
            print 'Added token:', token
            self.add_delivered_token(token)
        cache_dir_lock.acquire()
        fname = os.path.join(self._cache_dir, 'tokens', token)
        try:
            if self._file_was_created(token):
                cache_dir_lock.release()
                return response
            if not os.path.isfile(fname):
                fname = os.path.join(self._cache_dir, 'tokens', token)
                fp = open(fname, 'wb')
                # response.serialize()
                data = [response.content, response.status_code,
                        self.serialize_headers(response)]
                cPickle.dump(data, fp)
                fp.close()
                fname = os.path.join(self._cache_dir, 'file_infos', token)
                fp = open(fname, 'wb')
                cPickle.dump(True, fp)
                fp.close()
            else:
                pass
        finally:
            if cache_dir_lock._is_owned():
                cache_dir_lock.release()
        return response