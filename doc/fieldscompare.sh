#!/bin/bash 

dir_of_script="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

curl -s https://raw.githubusercontent.com/elastic/ecs/master/fields.yml | diff -u "$dir_of_script/fields.yml" -
