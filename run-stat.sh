#!/bin/bash

## TODO copy '-h' output here after template_management.py script is implemented
#args="$@"

# parse optional args
function join { local IFS="$1"; shift; echo "$*"; }
if [ "$1" ]; then
	conf_pattern="$(join ',' ${@:1})"
	echo $conf_pattern
	. .venv/bin/activate && python doc/genutil.py -a stat -p "$conf_pattern"
fi

