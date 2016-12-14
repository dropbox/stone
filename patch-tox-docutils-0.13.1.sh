#!/usr/bin/env bash

set -ex

MY_DIR="$( cd "$( dirname "${0}" )" && pwd )"
TOX_DIR="${MY_DIR}/.tox/docutils-0.13.1"
PATCH_DIR="$( find "${TOX_DIR}" -name docutils -type d )"
PATCH_FILE="${MY_DIR}/bug_270_2.patch"
cd "${PATCH_DIR}/.."
rm -fv docutils/frontend.pyc
patch -p1 <"${PATCH_FILE}"
