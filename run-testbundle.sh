#!/usr/bin/env bash

dir_of_script="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
testing_dir="$dir_of_script/testing"

usage() {
	echo
	echo 'Testen von Logstash-Filtern (d.h. *.conf Dateien mit dazugehoerigen JSON-Vorgaben innerhalb eines anzugebenden Testbundle-Ordners).'
	echo
	echo 'Benutzung:'
	echo '  '$(basename "$0")' [<testbundle-rootdir=testing>] [<pfadmuster1-zu-*.conf-files> <pfadmuster2-zu-*.conf-files> ...]'
	echo
	echo 'Beispiele:'
	echo '  1) '$(basename "$0")''
	echo '     => testet jede Conf in pipelines/*/*.conf gegen passenden JSON-Input in testing/pipelines/*/*.json'
	echo
	echo '  2) '$(basename "$0")' pipelines/*/*.conf'
	echo '     => wie 1) - hier wurde das Default-Pfadmuster zu den Confs explizit angegeben'
	echo
	echo '  3) '$(basename "$0")' testing'
	echo '     => wie 1) - hier wurde explizit angegeben, dass mit JSON-Inputs aus testing/pipelines/*/*.json zu testen ist'
	echo
	echo '  4) '$(basename "$0")' testing/myCustomJSONs pipelines/{filebeat,metricbeat}/ha*.conf'
	echo '     => testet jede Conf in pipelines/{filebeat,metricbeat}/ha*.conf gegen passenden JSON-Input aus testing/myCustomJSONs/pipelines/*.json'
	echo
	echo '  5) '$(basename "$0")' testing/myCustomJSONs pipelines/filebeat/ha*.conf pipelines/metricbeat/ha*.conf'
	echo '     => wie 4)'
	echo
	echo '  6) '$(basename "$0")' pipelines/{filebeat,metricbeat}/ha*.conf'
	echo '     => testet jede Conf in pipelines/{filebeat,metricbeat}/ha*.conf gegen passenden JSON-Input in testing/pipelines/*/*.json'
	echo
	echo 'Hinweis:'
	echo '     - Bash-Completion ist anwendbar'
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
		read -p "Der Ordner testing/logstash ist nicht vorhanden.  Jetzt initialisieren? (dauert ca. 3 Minuten) (j/y/n)" yn
		case $yn in
			[JjYy]* ) init; break;;
			[Nn]* ) exit;;
			* ) ;;
		esac
	done
fi

# print usage on parameter -h
while getopts ':h' option; do
	case "$option" in
		h) usage
		exit;;
		\?) echo "illegal option: -$OPTARG"
		usage
		exit;;
	esac
done
shift $((OPTIND - 1))


# parse optional testbundle and conf-pattern args
function join { local IFS="$1"; shift; echo "$*"; }
testbundle_dir="$1"
conf_pattern="pipelines/*/*.conf"
if [[ "$1" != testing* ]]; then
	testbundle_dir="testing"
	if [ "$1" ]; then
		conf_pattern="$(join , ${@:1})"
	fi
else 
	if [ "$2" ]; then
		conf_pattern="$(join , ${@:2})"
	fi
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
