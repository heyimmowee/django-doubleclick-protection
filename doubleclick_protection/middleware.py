# -*- coding: utf-8 -*-

"""Middleware class."""

import os
import time

from django.conf import settings
from django.middleware.csrf import get_token


HTML_CONTENT_TYPES = (
    'text/html',
    'application/xhtml+xml',)


class DoubleClickProtectionMiddleware(object):
    """Middleware to prevent multiple POST events with the same token."""
    
    def __init__(self):
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
                if not os.path.isdir(dir):
                    try:
                        os.makedirs(dir)
                    except OSError, err:
                        raise StandardError(
                            'Could\'nt create directory %s: %s'
                            % (dir, str(err)))
            #finally:
            #    cache_dir_lock.release()
    
    def add_token(self, token):
        pass
        
    def get_token(self, request):
        """Retrieves the current CSRF token from the request.
        
        :param request: :class:`HttpRequest`
        """
        return request.POST.get('csrfmiddlewaretoken', None)
        
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
                
    def story_body(self):
        """Saves the response into a file."""

    def process_request(self, request):
        # Check for request.user.is_anonymous() ?
        # Check for content-type?
        if request.method != 'POST':
            return
        token = self.get_token(request)
        if token is None:
            return

    #def process_response(self, request, response):
    #    pass
