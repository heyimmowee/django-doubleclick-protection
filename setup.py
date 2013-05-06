#!/usr/bin/env python

from setuptools import setup, find_packages

packages = find_packages(exclude=('tests',))

install_requires = [
    'setuptools',
    'Django']

tests_require = []

testing_extras = tests_require + [
    'nose',
    'coverage',
    'virtualenv']

docs_extras = [
    'Sphinx',
    'docutils']


setup(name='django-doubleclick-protection',
      version='0.1',
      description='Python Distribution Utilities',
      author='Henning Kage',
      author_email='henning.kage@gmail.com',
      url='http://github.com/hkage/django-doubleclick-protection/',
      packages=packages,
      install_requires=install_requires,
      extras_require={
          'testing':testing_extras,
          'docs':docs_extras,
          },
      tests_require=tests_require,
      test_suite='doubleclick_protection.tests',
     )