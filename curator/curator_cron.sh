#!/bin/bash
config="/etc/logstash/avm-git/curator/curator_config.yml"
action="/etc/logstash/avm-git/curator/actionfiles"
#
#
# Actions
curator --config $config $action/delete.yml

