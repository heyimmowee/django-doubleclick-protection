django-doubleclick-protection
=============================

A server-side attempt to prohibit double clicks in Django applications.

The idea behind this was born with a Turbogears project we wrote in our
company. We wanted to create a solution to solve the double-click
problem without relying on a client-side solution. `Martin Brochhaus`__
wrote the first version and I refactored it over the years, e.g. to
use the filesystem instead of a database variant. This is an attempt to
port the code to a reusable Django application.

Features
========

``django-doubleclick-protection`` uses Django's CSRF token middleware to prevent
multiple view calls with more than one click. First of all this application
will generate a new token for each request to make every request unique. No
form should be submitted more than once. Therefore every token will be saved
in the filesystem. Additionally the application will save the content from the
first response. If the user submits a form more than once a time, the token
will be recognized as already received and the middleware will return the old
response instead of calling the view multiple times.

|buildstatus|_

Installation
============

``django-doubleclick-protection`` is currently in development. There aren't any PyPi packages yet.

#. Get the latest version::

    $ git clone git://github.com/hkage/django-doubleclick-protection.git#egg=django-doubleclick-protection

#. Add ``django-doubleclick-protection`` to the list of installed apps:

.. code-block:: python

    INSTALLED_APPS = (
        # ...
        'doubleclick_protection',
        )

#. Add the middleware classes right after Django's CSRF middleware:

.. code-block:: python

    MIDDLEWARE_CLASSES = (
        # ...
        'django.middleware.csrf.CsrfViewMiddleware',
        'doubleclick_protection.middleware.CsrfTokenPerRequestMiddleware',
        'doubleclick_protection.middleware.DoubleClickProtectionMiddleware',
        # ...
        )

Settings
========

``DCLICK_CACHE_DIR``
  Directory for the tokens to be stored.

``DCLICK_MAX_TOKEN_AGE`` (Default 86400)
  Maximum token age (in seconds) before the token will be deleted.

__ https://github.com/mbrochh

Commands
========

``clear_tokens``

.. |buildstatus| image:: https://secure.travis-ci.org/hkage/django-doubleclick-protection.png?branch=master
.. _buildstatus: http://travis-ci.org/#!/hkage/django-doubleclick-protection