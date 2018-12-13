#!/bin/bash

## TODO copy '-h' output here after template_management.py script is implemented
args="$@"
. .venv/bin/activate && python doc/template-tools.py $args