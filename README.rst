django-doubleclick-protection
=============================

A server-side attempt to prohibit double clicks in Django applications.

Installation
============

``django-doubleclick-protection`` is currently in development. There aren't any PyPi packages yet.

#. Get the latest version::

	$ git clone git://github.com/hkage/django-doubleclick-protection.git#egg=django-doubleclick-protection
	
#. Add ``django-doubleclick-protection`` to the list of installed apps::

	INSTALLED_APPS = (
		# ...,
		'doubleclick_protection'
		)

Settings
========