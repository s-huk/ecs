#!/bin/bash

## TODO copy '-h' output here after template_management.py script is implemented
#args="$@"

# parse optional args
function join { local IFS="$1"; shift; echo "$*"; }
conf_pattern="pipelines/*/*.conf"
if [ "$1" ]; then
	conf_pattern="$(join ',' ${@:1})"
fi

. .venv/bin/activate && python src/genutil.py -a show -p "$conf_pattern"
