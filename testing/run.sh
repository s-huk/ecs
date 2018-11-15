#!/usr/bin/env bash

dir_of_script="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

if ! [[ "$PATH" =~ "logstash/vendor/jruby/bin" ]]; then 
	export PATH="$dir_of_script/logstash/vendor/jruby/bin:$PATH"
fi

cd $dir_of_script/logstash
echo "Logstash dir: $dir_of_script/logstash"
bundle exec rspec "$dir_of_script/filter_spec.rb"
