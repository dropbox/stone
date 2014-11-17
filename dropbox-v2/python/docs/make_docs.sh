#!/bin/sh
export PYTHONPATH=..
make html
#xdg-open _build/html/index.html
echo "See docs here: _build/html/index.html"
