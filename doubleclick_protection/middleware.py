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


logger = logging.getLogger('doubleclick_protection')

cache_dir_lock = threading.RLock()
before_main_lock = threading.RLock()

HTML_CONTENT_TYPES = (
    'text/html',
    'text/plain',
    'application/xml',
    'application/xhtml+xml',)

MAX_WAIT = 5  # in seconds (30)

DCLICK_CACHE_DIR = getattr(settings, 'DCLICK_CACHE_DIR', '/tmp/token_cache')


class CsrfTokenPerRequestMiddleware(object):
    """Middleware to generate a new CSRF token per request."""

    def process_view(self, request, callback, callback_args, callback_kwargs):
        token = _get_new_csrf_key()
        logger.debug('Generated token %s' % token)
        request.META['CSRF_COOKIE'] = token


class DoubleClickProtectionMiddleware(object):
    """Middleware to prevent multiple POST events with the same token."""

    def __init__(self):
        """Constructor"""
        self._cache_dir = DCLICK_CACHE_DIR
        self._create_directories()

    def _create_directories(self):
        """Creates all necessary directories to store tokens."""
        dirs = (self._cache_dir,
                os.path.join(self._cache_dir, 'tokens'),
                os.path.join(self._cache_dir, 'delivered_tokens'),
                os.path.join(self._cache_dir, 'file_infos'),
                os.path.join(self._cache_dir, 'received_tokens'))
        for dir in dirs:
            with cache_dir_lock:
                if os.path.isdir(dir):
                    continue
                try:
                    os.makedirs(dir)
                except OSError, err:
                    raise StandardError(
                        'Could\'nt create directory %s: %s'
                        % (dir, str(err)))

    def _file_was_created(self, token):
        if self.token_exists('received_tokens', token):
            fname = self.get_filename('file_infos', token)
            fp = open(fname, 'rb')
            data = cPickle.load(fp)
            fp.close()
            return bool(data)
        return False

    def _file_was_saved(self, token):
        fname = self.get_filename('file_infos', token)
        fp = open(fname, 'rb')
        data = cPickle.load(fp)
        fp.close()
        return data == True

    def _token_was_delivered(self, token):
        """Check, whether a token as already been delivered."""
        return self.token_exists('delivered_tokens', token)

    def add_delivered_token(self, token):
        """Mark a token as delivered.

        :param token:
        """
        fname = self.get_filename('tokens', token)
        if os.path.isfile(fname):
            return False
        if not self.token_exists('delivered_tokens', token):
            fname = self.get_filename('delivered_tokens', token)
            try:
                open(fname, 'w').close()
            except OSError, err:
                raise StandardError(
                    ('Could\'nt write delivered token %s') % str(err))
            return True
        return False

    def add_received_token(self, token):
        """Mark a token as received.

        :param token:
        """
        fname = self.get_filename('received_tokens', token)
        try:
            open(fname, 'w').close()
        except OSError, err:
            raise StandardError(
                'Error writing the information of a received token: %s'
                % str(err))

    def get_filename(self, directory, token):
        """Returns the complete filename for a token from a specific dir.

        :param directory:
        :param token:
        :returns: Complete path of the token file
        """
        return os.path.join(self._cache_dir, directory, token)

    def is_static_request(self, request):
        """Checks whether the request content type is static.

        Although a productive Django application won't serve static content,
        we want to pass all requests, that are not HTML content types.

        :param request:
        :returns: ``True`` or ``False``
        """
        return request.META['CONTENT_TYPE'] not in HTML_CONTENT_TYPES

    def token_exists(self, dir, token):
        """Checks, whether the token exists as a file.

        :param dir:
        :param token:
        :returns ``True`` or ``False``
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
        fname = self.get_filename(dir, token)
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
        # Check for content-type?
        if request.method != 'POST':
            return None
        token = request.POST.get('csrfmiddlewaretoken', None)
        if token is None:
            return None
        logger.debug('Got token %s' % token)
        if not self._token_was_delivered(token):
            return HttpResponseForbidden('Received unknown token')
        with before_main_lock:
            if self.token_exists('received_tokens', token):
                # starting_time = time.time()
                # while not self._file_was_saved(token):
                #    delta = time.time() - starting_time
                #    if delta > MAX_WAIT:
                #        logger.warning(
                #            'Thread %s had to wait more than %s seconds.'
                #            % (thread.get_ident(), MAX_WAIT))
                #        return
                #    threading._sleep(1)
                fname = self.get_filename('tokens', token)
                if os.path.isfile(fname):
                    logger.debug('Returning saved response')
                    fp = open(fname, 'rb')
                    data = cPickle.load(fp)
                    fp.close()
                    return HttpResponse(content=data[0], status=data[1])
                else:
                    logger.warning('Response not found')
                    return None
            else:
                logger.debug('Add received token: %s' % token)
                fname = self.get_filename('file_infos', token)
                fp = open(fname, 'w')
                cPickle.dump(False, fp)
                fp.close()
                self.add_received_token(token)
        return None

    def process_response(self, request, response):
        # if request.user.is_anonymous():
        #    return response
        if self.is_static_request(request):
            return response
        token = request.META.get('CSRF_COOKIE', None)
        if token is None:
            return response
        if not self.token_exists('delivered_tokens', token):
            logger.debug('Added token: %s', token)
            self.add_delivered_token(token)
        cache_dir_lock.acquire()
        fname = self.get_filename('tokens', token)
        try:
            if self._file_was_created(token):
                cache_dir_lock.release()
                return response
            if not os.path.isfile(fname):
                fname = self.get_filename('tokens', token)
                fp = open(fname, 'wb')
                data = [response.content, response.status_code,
                        self.serialize_headers(response)]
                cPickle.dump(data, fp)
                fp.close()
                fname = self.get_filename('file_infos', token)
                fp = open(fname, 'wb')
                cPickle.dump(True, fp)
                fp.close()
            else:
                pass
        finally:
            if cache_dir_lock._is_owned():
                cache_dir_lock.release()
        return response
