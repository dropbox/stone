# Ensure setuptools is available
from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup

install_reqs = ['ply>=3.4',
                'six>=1.3.0']

dist = setup(
    name='babelapi',
    version='0.1',
    description='BabelAPI',
    author='Dropbox',
    author_email='dev-platform@dropbox.com',
    url='http://www.dropbox.com/developers',
    install_requires=install_reqs,
    license='LICENSE',
    zip_safe=False,
    packages=['babelapi',
              'babelapi.babel',
              'babelapi.generator',
              'babelapi.lang'],
    long_description=open('README.rst').read(),
    platforms=['CPython 2.6', 'CPython 2.7'],      
    entry_points = {
        'console_scripts': ['babelapi=babelapi.cli:main'],
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
