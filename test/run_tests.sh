#!/bin/bash

# TODO(kelkabany): Ignore system-wide babelapi installations.

# If a test suite returns an error, do not continue to the next one.
set -e

# Enforce that the script is run from within the test folder so that
# our PYTHONPATH is set correctly.
if [[ "$PWD" != */test ]]
then
    echo "Script must be executed from within test folder." 
    exit 1
fi

# Do not use the -s or -t flag for nose2. It requires our test files
# to be in Python packages.
echo "Running tests for babelapi package"
PYTHONPATH=.. python2.7 -m nose2

echo
echo "Running tests for babelapi package using Python 3"
PYTHONPATH=.. python3 -m nose2

echo
echo "Running tests for Python generator"
(cd ../generator/python && PYTHONPATH=../.. python2.7 -m nose2)

echo
echo "Running tests for Python generator using Python 3"
(cd ../generator/python && PYTHONPATH=../.. python3 -m nose2)
