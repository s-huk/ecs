import argparse
import json
from datetime import datetime
from confluent_kafka import Consumer, KafkaError, TIMESTAMP_NOT_AVAILABLE, OFFSET_END
from jsonpath_rw import parse
import re

# arg parsing
parser = argparse.ArgumentParser(description='Run a kafka consumer for extracting testing data.')
parser.add_argument('-c', '--cluster', type=str, dest='cluster', help="Kafka cluster to extract data from. Defaults to 'test'.", choices=["test","prod","local"], default="test")
parser.add_argument('-t', '--topic', type=str, required=True, dest='topic', help="Topic name to extract data from.")
parser.add_argument('-g', '--groupid', type=str, dest='groupid', help="Consumer group.id to use.", default="elop-test-consumer")
parser.add_argument('-m', '--max-records', type=int, dest='max_records', help="Max records to read. Defaults to 1. 0 means infinite.", default=1)
parser.add_argument('-r', '--rewind', type=int, dest='rewind', help="Rewind # offsets relatively to current tail.")
parser.add_argument('-f', '--filter', type=str, dest='filter', help="Filter for JSON payload using <JSON_Path>=<Regex>.")
parser.add_argument('-p', '--prettify', type=bool, dest='prettify', help="Prettify a JSON payload", default=False, nargs='?', const=True)

args = parser.parse_args()
print("Called with arguments: %s" % args)

# cluster coordinates
cluster_coordinates = dict(
  prod="kafka-sv-01.avm.de:9094,kafka-sv-02.avm.de:9094,kafka-sv-03.avm.de:9094",
  test="t-kafka-sv-01.avm.de:9094,t-kafka-sv-02.avm.de:9094,t-kafka-sv-03.avm.de:9094",
  local="localhost:9092"
)

c = Consumer({
  #'debug': "consumer,cgrp,topic,fetch",
  'bootstrap.servers': cluster_coordinates[args.cluster],
  'group.id': args.groupid,
  'auto.offset.reset': 'latest',
  'security.protocol': 'SASL_PLAINTEXT',
  'sasl.mechanism': 'PLAIN',
  'sasl.username': 'ksu',
  'sasl.password': 'aa7rae#ng'
})

# actual consume method
def consume():

  # subscribe including seek
  if not args.rewind:
    args.rewind = 1 + args.max_records
  def assign_handler(c, partitions):
      for p in partitions:
        l_offset, h_offset = c.get_watermark_offsets(p)
        req_offset = h_offset - args.rewind
        p.offset = req_offset if req_offset > l_offset else l_offset
      print('\nAssign', partitions)
      c.assign(partitions)
  c.subscribe([args.topic], on_assign=assign_handler)

  counter = 1

  while True:
    msg = c.poll(1.0)
    if msg is None:
        continue
    if msg.error():
        if msg.error().code() == KafkaError._PARTITION_EOF:
            continue
        else:
            print(msg.error())
            break

    # print message
    msg_ts = None
    if msg.timestamp()[0] != TIMESTAMP_NOT_AVAILABLE:
      msg_ts = datetime.fromtimestamp(msg.timestamp()[1]/1000).strftime('%Y-%m-%d %H:%M:%S')

    msg_value = msg.value().decode('utf-8')
    if args.prettify:
      try:
        msg_value = json.dumps(json.loads(msg_value), indent=2, sort_keys=True)
      except JSONDecodeError:
        pass

    # filter handling
    matches = not args.filter
    if args.filter:
      filter = args.filter.split("=")
      jsonpath_expr = parse(filter[0])
      values = [match.value for match in jsonpath_expr.find(json.loads(msg_value))]
      #print("%s = %s = %s" % (filter, jsonpath_expr, values))
      for v in values:
        if re.match(r'%s' % filter[1], str(v)):
          matches = True
          break

    if not matches:
      continue

    print("""
==========================
topic={}
partition={}
offset={}
timestamp={}
key={}
--------------------------
{}
==========================
""".format(
      msg.topic(),
      msg.partition(),
      msg.offset(),
      msg_ts,
      msg.key().decode('utf-8'),
      msg_value
    )
  )

    if args.max_records > 0 and args.max_records == counter:
      break

    counter += 1


try:
  consume()
except KeyboardInterrupt:
  print('Interrupted')
finally:
  c.close();