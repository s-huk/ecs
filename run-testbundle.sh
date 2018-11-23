#!/usr/bin/env bash

dir_of_script="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
testing_dir="$dir_of_script/testing"

usage() {
	echo
	echo 'Testen von Logstash-Filtern (d.h. *.conf Dateien mit dazugehoerigen JSON-Vorgaben innerhalb eines anzugebenden Testbundle-Ordners).'
	echo
	echo 'Benutzung:'
	echo '  $(basename '$0') <testbundle-rootdir> [<pfadmuster1-zu-*.conf-files> <pfadmuster2-zu-*.conf-files> ...]'
	echo
	echo 'Beispiele:'
	echo '  1) $(basename '$0') testing/bundle01'
	echo '     => testet jede Conf in pipelines/*/*.conf gegen passenden JSON-Input in testing/bundle01/pipelines/*/*.json'
	echo
	echo '  2) $(basename '$0') testing/bundle01 pipelines/*/*.conf'
	echo '     => wie 1) - hier wurde das Default-Pfadmuster zu den Configs explizit angegeben'
	echo
	echo '  3) $(basename '$0') testing/bundle01 pipelines/filebeat/ha*.conf'
	echo '     => testet jede Conf in pipelines/filebeat/ha*.conf gegen passenden JSON-Input in testing/bundle01/pipelines/filebeat/ha*.json'
	echo
	echo '  4) $(basename '$0') testing/bundle01 pipelines/filebeat/ha*.conf pipelines/filebeat/fail2*.conf'
	echo '     => testet jede Conf in pipelines/filebeat/ha*.conf gegen passenden JSON-Input in testing/bundle01/pipelines/filebeat/ha*.json'
	echo
	echo '  5) $(basename '$0') testing/bundle01 pipelines/filebeat/{ha,fail}*.conf'
	echo '     => wie 4)'
	echo
	echo 'Hinweis:'
	echo '     Bash-Completion ist anwendbar'
	echo
	exit 1
}

# initialization of the test environment
init() {
	cd $testing_dir
	echo "Working directory: $testing_dir"
	rm -rf $testing_dir/logstash*
	wget https://artifacts.elastic.co/downloads/logstash/logstash-6.5.0.tar.gz
	tar xfz logstash-6.5.0.tar.gz
	rm logstash*tar.gz
	mv logstash-6* logstash
	cd logstash
	./bin/logstash-plugin install --development
	cp logstash-core/versions-gem-copy.yml logstash-core-plugin-api
	if ! [[ "$PATH" =~ "logstash/vendor/jruby/bin" ]]; then 
		export PATH="$testing_dir/logstash/vendor/jruby/bin:$PATH"
	fi

	jruby -S gem install bundler
	echo 'gem "diffy", "~> 3.2.0"' >> Gemfile
	#echo 'gem "logstash-core-plugin-api", "~> 0.0.0"' >> Gemfile
	bundle install
	#gem install logstash-core-plugin-api
}

# check necessity for initialization
if [ ! -d "$testing_dir/logstash" ]; then
	while true; do
		read -p "Die Logstash-Test-Umgebung ist nicht initialisiert.  Jetzt initialisieren? (dauert ca. 3 Minuten) (j/y/n)" yn
		case $yn in
			[JjYy]* ) init; break;;
			[Nn]* ) exit;;
			* ) ;;
		esac
	done
fi


# parse first testbundle arg
if [[ "$1" != testing* ]]; then
	echo "missing test bundle directory"
	usage
fi
testbundle_dir="$1"
if [ -z $testbundle_dir ]
	then
	echo "missing test bundle directory"
	usage
fi

# define the set of all resulting *.conf path patterns
function join { local IFS="$1"; shift; echo "$*"; }
conf_pattern="pipelines/*/*.conf"
if [ "$2" ]; then
	conf_pattern="$(join , ${@:2})"
fi


# console reporting
echo "Logstash dir: $testing_dir/logstash"
echo
echo "Testbundle-Verzeichnis: $testbundle_dir"
echo
echo -e "Conf-Pattern(s): \n${conf_pattern//,/'\n'}"
echo


# communicate the path patterns to the ruby script
export LOGSTASH_TESTING_CONF_PATTERN="{$conf_pattern}"
export LOGSTASH_TESTING_TESTBUNDLE_DIR="$testbundle_dir"

if ! [[ "$PATH" =~ "logstash/vendor/jruby/bin" ]]; then 
	export PATH="$testing_dir/logstash/vendor/jruby/bin:$PATH"
#	export PATH="$testing_dir/logstash/vendor/bundle/jruby/bin:$PATH"
	export LOGSTASH_HOME="$testing_dir/logstash"
fi

# run testbundle
cd $testing_dir/logstash
bundle exec rspec -fd "$testing_dir/filter_spec.rb"
