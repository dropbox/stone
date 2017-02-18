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

install_reqs = [
    'ply>=3.4',
    'six>=1.3.0',
]

setup_requires = [
    'pytest-runner',
]

test_reqs = [
    'pytest',
]

# WARNING: This imposes limitations on test/requirements.txt such that the
# full Pip syntax is not supported. See also
# <http://stackoverflow.com/questions/14399534/>.
with open('test/requirements.txt') as f:
    test_reqs += f.read().splitlines()

with open('LICENSE') as f:
    LICENSE = f.read()

with open('README.rst') as f:
    README = f.read()

dist = setup(
    name='stone',
    version='0.1',
    description='Stone is an interface description language (IDL) for APIs.',
    author='Ken Elkabany',
    author_email='kelkabany@dropbox.com',
    maintainer='Dropbox',
    maintainer_email='dev-platform@dropbox.com',
    url='https://github.com/dropbox/stone',
    install_requires=install_reqs,
    setup_requires=setup_requires,
    tests_require=test_reqs,
    license=LICENSE,
    zip_safe=False,
    packages=['stone',
              'stone.lang',
              'stone.target',
              'stone.target.python_rsrc'],
    long_description=README,
    platforms=['CPython 2.7', 'CPython 3.4', 'CPython 3.5'],
    entry_points={
        'console_scripts': ['stone=stone.cli:main'],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Code Generators',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
