#!/bin/sh
# Tests for the bookended-thinking instrument. Independent of the moop build:
# `make` and `make test` at the repository root do not touch this directory.
set -e
cd "$(dirname "$0")"
python3 -m unittest discover -s tests -t . "$@"
python3 bt.py check >/dev/null
echo "bt check: ontology loads, prompts leak no predictions, drills parse"
