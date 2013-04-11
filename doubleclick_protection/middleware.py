# -*- coding: utf-8 -*-

# TODO(hk): Generate new token per request, e.g.:
#   request.META["CSRF_COOKIE"] = _get_new_csrf_key()

"""Middleware class."""

import cPickle
import os
import time

from django.conf import settings
from django.middleware.csrf import get_token, _get_new_csrf_key


HTML_CONTENT_TYPES = (
    'text/html',
    'application/xhtml+xml',)


class CsrfTokenPerRequestMiddleware(object):
    """Middleware to generate a new CSRF token per request."""

    def process_view(self, request, callback, callback_args, callback_kwargs):
        # Overwrite Django's token. We want a new token per request.
        #import ipdb; ipdb.set_trace()
        #try:
        #    del request.COOKIES[settings.CSRF_COOKIE_NAME]
        #    #del request.META['CSRF_COOKIE']
        #except KeyError:
        #    pass
        request.META["CSRF_COOKIE"] = _get_new_csrf_key()


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
            #cache_dir_lock.acquire()
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
                pass
            #    cache_dir_lock.release()

    def _file_was_created(self, token):
        if self.token_exists('received_tokens', token):
            fname = os.path.join(self._cache_dir, 'file_infos', token)
            fp = open(fname, 'rb')
            data = cPickle.load(fp)
            fp.close()
            return bool(data)
        return False

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
                    ('Could\'t write delivered token %s') % str(err))
            return True
        return False

    def add_received_token(self, token):
        pass

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

    def process_request(self, request):
        # Check for request.user.is_anonymous() ?
        # Check for content-type?
        if request.method != 'POST':
            return
        token = request.POST.get('csrfmiddlewaretoken', None)
        if token is None:
            return

    def process_response(self, request, response):
        if request.method != 'GET':
            return response
        token = request.COOKIES.get('csrftoken')
        if not self.token_exists('delivered_tokens', token):
            self.add_delivered_token(token)
        #import ipdb; ipdb.set_trace()
        fname = os.path.join(self._cache_dir, 'tokens', token)
        try:
            # File was already created
            if self._file_was_created(token):
                return response
            if not os.path.isfile(fname):
                fname = os.path.join(self._cache_dir, 'tokens', token)
                fp = open(fname, 'wb')
                data = [response.serialize(), response.status_code,
                        response.serialize_headers()]
                cPickle.dump(data, fp)
                fp.close()
                fname = os.path.join(self._cache_dir, 'file_infos', token)
                fp = open(fname, 'wb')
                cPickle.dump(True, fp)
                fp.close()
            else:
                pass
        finally:
            pass

        return response