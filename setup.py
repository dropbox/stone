# Don't import unicode_literals because of a bug in py2 setuptools
# where package_data is expected to be str and not unicode.
from __future__ import absolute_import, division, print_function

import sys

from setuptools import setup

try:
    from ez_setup import use_setuptools

    use_setuptools()
except ImportError:
    # Try to use ez_setup, but if not, continue anyway. The import is known
    # to fail when installing from a tar.gz.
    print("Could not import ez_setup", file=sys.stderr)


install_reqs = [
    "ply >= 3.4",
    "six >= 1.3.0",
]

with open("README.rst") as f:
    README = f.read()

dist = setup(
    name="stone",
    version="3.0.0",
    install_requires=install_reqs,
    entry_points={"console_scripts": ["stone=stone.cli:main"]},
    packages=[
        "stone",
        "stone.backends",
        "stone.backends.python_rsrc",
        "stone.frontend",
        "stone.ir",
    ],
    package_data={"stone": ["py.typed"]},
    zip_safe=False,
    author_email="kelkabany@dropbox.com",
    author="Ken Elkabany",
    description="Stone is an interface description language (IDL) for APIs.",
    license="MIT License",
    long_description=README,
    long_description_content_type="text/x-rst",
    maintainer_email="api-platform@dropbox.com",
    maintainer="Dropbox",
    url="https://github.com/dropbox/stone",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
