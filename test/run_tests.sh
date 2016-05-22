#!/bin/bash

# TODO(kelkabany): Ignore system-wide stone installations.

# If a test suite returns an error, do not continue to the next one.
set -e

# Enforce that the script is run from within the test folder so that
# our PYTHONPATH is set correctly.
if [[ "$PWD" != */test ]]
then
    echo "Script must be executed from within test folder." 
    exit 1
fi

echo "Running tests for stone package"
PYTHONPATH=.. python2.7 -m pytest

echo
echo "Running tests for stone package using Python 3"
PYTHONPATH=.. python3 -m pytest

echo
echo "Running tests for Python generator"
(cd ../generator/python && PYTHONPATH=../.. python2.7 -m pytest)

echo
echo "Running tests for Python generator using Python 3"
(cd ../generator/python && PYTHONPATH=../.. python3 -m pytest)
