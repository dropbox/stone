# Don't import unicode_literals because of a bug in py2 setuptools
# where package_data is expected to be str and not unicode.
from __future__ import absolute_import, division, print_function

import sys

try:
    from ez_setup import use_setuptools
    use_setuptools()
except ImportError:
    # Try to use ez_setup, but if not, continue anyway. The import is known
    # to fail when installing from a tar.gz.
    print('Could not import ez_setup', file=sys.stderr)

from setuptools import setup

install_reqs = ['ply>=3.4',
                'six>=1.3.0']

dist = setup(
    name='stone',
    version='0.1',
    description='Stone is an interface description language (IDL) for APIs.',
    author='Dropbox',
    author_email='dev-platform@dropbox.com',
    url='http://www.dropbox.com/developers',
    install_requires=install_reqs,
    license='LICENSE',
    zip_safe=False,
    packages=['stone',
              'stone.stone',
              'stone.lang'],
    long_description=open('README.rst').read(),
    platforms=['CPython 2.6', 'CPython 2.7'],
    entry_points={
        'console_scripts': ['stone=stone.cli:main'],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
