#!/usr/bin/env bash

dir_of_script="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

if ! [[ "$PATH" =~ "logstash/vendor/jruby/bin" ]]; then 
	export PATH="$dir_of_script/logstash/vendor/jruby/bin:$PATH"
#	export PATH="$dir_of_script/logstash/vendor/bundle/jruby/bin:$PATH"
	export LOGSTASH_HOME="$dir_of_script/logstash"
fi

cd $dir_of_script/logstash
echo "Logstash dir: $dir_of_script/logstash"
bundle exec rspec -fd "$dir_of_script/filter_spec.rb"
