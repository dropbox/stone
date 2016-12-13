# Don't import unicode_literals because of a bug in py2 setuptools
# where package_data is expected to be str and not unicode.
from __future__ import absolute_import, division, print_function

from setuptools import setup

dist = setup(
    name='stone',
    version='0.1',
    description='DESCRIPTION',
    author='Ken Elkabany',
    author_email='kelkabany@dropbox.com',
    url='https://github.com/dropbox/stone',
    install_requires=[],
    license='LICENSE',
    packages=['stone'],
    long_description='README',
)
