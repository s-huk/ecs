#!/usr/bin/env bash

dir_of_script="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
cd $dir_of_script
wget https://artifacts.elastic.co/downloads/logstash/logstash-6.5.0.tar.gz
tar xfz logstash-6.5.0.tar.gz
rm logstash*tar.gz
mv logstash-6* logstash
cd logstash
./bin/logstash-plugin install --development
cp logstash-core/versions-gem-copy.yml logstash-core-plugin-api
if ! [[ "$PATH" =~ "logstash/vendor/jruby/bin" ]]; then 
	export PATH="$dir_of_script/logstash/vendor/jruby/bin:$PATH"
fi
# ??? apt-get install jruby 
jruby -S gem install bundler
bundle install
gem install logstash-core-plugin-api

