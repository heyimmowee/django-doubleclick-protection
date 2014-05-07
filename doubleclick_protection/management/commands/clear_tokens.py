"""Command to cleanup expired tokens."""

import os
import time

from django.conf import settings
from django.core.management.base import BaseCommand


DCLICK_MAX_TOKEN_AGE = getattr(settings, 'DCLICK_MAX_TOKEN_AGE', 86400)
DCLICK_CACHE_DIR = getattr(settings, 'DCLICK_CACHE_DIR', '/tmp/token_cache')


class Command(BaseCommand):

    help = 'Cleanup expired token tokens'

    def __init__(self, *args, **kwargs):
        self._cache_dir = DCLICK_CACHE_DIR
        self._max_token_age = DCLICK_MAX_TOKEN_AGE
        BaseCommand.__init__(self, *args, **kwargs)

    def handle(self, *args, **options):
        for dirpath, dirnames, filenames in os.walk(self._cache_dir):
            for file in filenames:
                fname = os.path.abspath(os.path.join(dirpath, file))
                delta = time.time() - os.stat(fname).st_mtime
                if delta > self._max_token_age:
                    os.remove(fname)
