#!/bin/bash
config="/etc/logstash/avm-git/curator/curator_config.yml"
#
#
# Actions
for action in /etc/logstash/avm-git/curator/actionfiles/*;
do
	curator --config $config $action
done


