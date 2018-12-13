import argparse


# arg parsing
parser = argparse.ArgumentParser(description='Run tooling related to elastic templaes .')
parser.add_argument('-a', '--action', type=str, required=True, dest='action', help="Action to run. 'show' will print the final template to stdout.", choices=[ "show" ], default="show")
parser.add_argument('-p', '--pipeline', type=str, required=True, dest='pipeline', help="Path to pipeline conf to run against. Should be relative to the projects root folder.")

args = parser.parse_args()
print("Called with arguments: %s" % args)