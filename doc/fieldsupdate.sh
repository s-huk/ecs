#!/bin/bash 

dir_of_script="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

wget -q https://raw.githubusercontent.com/elastic/ecs/master/fields.yml -O "$dir_of_script/fields.yml"
