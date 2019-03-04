#!/bin/bash

# $ ./run-kafka-consumer.sh -h
# usage: kafka_consumer.py [-h] [-c {test,prod,local}] -t TOPIC [-g GROUPID]
#                          [-m MAX_RECORDS] [-r REWIND] [-f FILTER]
#                          [-p [PRETTIFY]]
#
# Run a kafka consumer for extracting testing data.
#
# optional arguments:
#   -h, --help            show this help message and exit
#   -c {test,prod,local}, --cluster {test,prod,local}
#                         Kafka cluster to extract data from. Defaults to
#                         'test'.
#   -t TOPIC, --topic TOPIC
#                         Topic name to extract data from.
#   -g GROUPID, --groupid GROUPID
#                         Consumer group.id to use.
#   -m MAX_RECORDS, --max-records MAX_RECORDS
#                         Max records to read. Defaults to 1. 0 means infinite.
#   -r REWIND, --rewind REWIND
#                         Rewind # offsets relatively to current tail.
#   -f FILTER, --filter FILTER
#                         Filter for JSON payload using <JSON_Path>=<Regex>.
#   -p [PRETTIFY], --prettify [PRETTIFY]
#                         Prettify a JSON payload
args="$@"
. .venv/bin/activate && python src/kafka_consumer.py $args
