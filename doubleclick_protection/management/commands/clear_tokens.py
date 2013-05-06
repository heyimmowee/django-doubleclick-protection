"""Command to cleanup expired tokens."""

import os
import time

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    help = 'Cleanup expired token tokens'

    def __init__(self, *args, **kwargs):
        self._cache_dir = settings.DCLICK_CACHE_DIR
        try:
            max_age = settings.DCLICK_MAX_TOKEN_AGEE
        except AttributeError:
            max_age = 86400
        self._max_token_age = max_age
        BaseCommand.__init__(self, *args, **kwargs)

    def handle(self, *args, **options):
        for dirpath, dirnames, filenames in os.walk(self._cache_dir):
            for file in filenames:
                fname = os.path.abspath(os.path.join(dirpath, file))
                delta = time.time() - os.stat(fname).st_mtime
                if delta > self._max_token_age:
                    os.remove(fname)
