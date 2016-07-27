#!/bin/bash -eux

EXCLUDE="(^example|ez_setup.py)"

# Include all Python files registered in Git, that don't occur in $EXCLUDE.
INCLUDE=$(git ls-files "$@" | grep '\.py$' | egrep -v "$EXCLUDE" | tr '\n' '\0' | xargs -0 | cat)

mypy --strict-optional --silent-imports --fast-parser $INCLUDE
