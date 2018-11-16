#!/usr/bin/env bash

dir_of_script="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
cd $dir_of_script
echo "Working directory: $dir_of_script"
rm -rf $dir_of_script/logstash*
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
echo 'gem "diffy", "~> 3.2.0"' >> Gemfile
#echo 'gem "logstash-core-plugin-api", "~> 0.0.0"' >> Gemfile
bundle install
#gem install logstash-core-plugin-api
#gem install diffy
