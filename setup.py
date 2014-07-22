# Ensure setuptools is available
from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup

install_reqs = ['jinja2>=2.7.0']

dist = setup(
    name='babelsdk',
    version='0.1',
    description='BabelSDK',      
    author='Dropbox',
    author_email='dev-platform@dropbox.com',
    url='http://www.dropbox.com/developers',
    install_requires=install_reqs,
    license='LICENSE',
    zip_safe=False,
    packages=['babelsdk',
              'babelsdk.babel',
              'babelsdk.generator',
              'babelsdk.lang'],
    long_description=open('README.rst').read(),
    platforms=['CPython 2.6', 'CPython 2.7'],      
    entry_points = {
        'console_scripts': ['babelsdk=babelsdk.cli:main'],
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
