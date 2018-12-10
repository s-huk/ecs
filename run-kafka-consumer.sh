#!/bin/bash

args="$@"
. .venv/bin/activate && python testing/kafka_consumer.py $args