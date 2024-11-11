# Don't import unicode_literals because of a bug in py2 setuptools
# where package_data is expected to be str and not unicode.

import sys

try:
    from ez_setup import use_setuptools
    use_setuptools()
except ImportError:
    # Try to use ez_setup, but if not, continue anyway. The import is known
    # to fail when installing from a tar.gz.
    print('Could not import ez_setup', file=sys.stderr)

from setuptools import setup

# WARNING: This imposes limitations on requirements.txt such that the
# full Pip syntax is not supported. See also
# <http://stackoverflow.com/questions/14399534/>.
install_reqs = []
with open('requirements.txt') as f:  # pylint: disable=W1514
    install_reqs += f.read().splitlines()

setup_requires = [
    'pytest-runner == 5.3.2',
]

# WARNING: This imposes limitations on test/requirements.txt such that the
# full Pip syntax is not supported. See also
# <http://stackoverflow.com/questions/14399534/>.
test_reqs = []
with open('test/requirements.txt') as f:  # pylint: disable=W1514
    test_reqs += f.read().splitlines()

with open('README.rst') as f:  # pylint: disable=W1514
    README = f.read()

dist = setup(
    name='stone',
    version='3.3.8',
    install_requires=install_reqs,
    setup_requires=setup_requires,
    tests_require=test_reqs,
    entry_points={
        'console_scripts': ['stone=stone.cli:main'],
    },
    packages=[
        'stone',
        'stone.backends',
        'stone.backends.python_rsrc',
        'stone.frontend',
        'stone.ir',
    ],
    package_data={
        'stone': ['py.typed'],
    },
    zip_safe=False,
    author_email='kelkabany@dropbox.com',
    author='Ken Elkabany',
    description='Stone is an interface description language (IDL) for APIs.',
    license='MIT License',
    long_description=README,
    long_description_content_type='text/x-rst',
    maintainer_email='api-platform@dropbox.com',
    maintainer='Dropbox',
    url='https://github.com/dropbox/stone',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Code Generators',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
