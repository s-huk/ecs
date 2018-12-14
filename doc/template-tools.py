import argparse
import os
import sys
import yaml 
import glob 
import json
from functools import reduce

# expands reusable fields at places expected (as designated by reusable property)
def expand_reusable_fields(f):
    def expand_reusable_helper(f):
        if isinstance(f, dict):
            if "reusable" in f and "expected" in f["reusable"]:
                reusable = f["reusable"]
                for name_expected in reusable["expected"]:
                    if "top_level" in reusable and reusable["top_level"]==True and "fields" in root:
                        root["fields"].append( {k:v for (k,v) in f.items() if not k=="reusable"} )
                    for d in root:
                        if d["name"] == name_expected and "fields" in d:
                            d["fields"].append( {k:v for (k,v) in f.items() if not k=="reusable"} )
            if "fields" in f:
                expand_reusable_helper(f["fields"])
        elif isinstance(f, list):
            for g in f:
                expand_reusable_helper(g)
    
    root = f.copy()
    expand_reusable_helper(root)
    return [{k:v for (k,v) in d.items() if not k=="reusable"} for d in root if not "reusable" in d or ("top_level" in d["reusable"] and d["reusable"]["top_level"]==True)]



def prune_fields(f, prefix):
    if isinstance(f, dict):
        f.pop("title", None)
        f.pop("description", None)
        f.pop("footnote", None)
        f.pop("example", None)
        f.pop("level", None)
        f.pop("group", None)
        f.pop("required", None)
        assert_key_existence(f, "name")
        if "multi_fields" in f:
            prune_fields(f["multi_fields"], f["name"])
        if "fields" in f:
            f.pop("type", None)
            prune_fields(f["fields"], "" if f["name"]=="base" else f["name"])
        else:
            assert_key_existence(f, "type")
    elif isinstance(f, list):
        for g in f:
            prune_fields(g, prefix)



def assert_key_existence(field, key):
    if key in field.keys():
        field[key] = str(field[key]).strip() # Remove leading/trailing spaces and newlines 
    else:
        if not "fields" in field.keys() or not isinstance(field["fields"], list):
            raise("key " + key + " does not exist")



def conv_fields_to_mapping(o):
    f = o.copy()
    if isinstance(f, dict) and "fields" in f:
        f["properties"] = conv_fields_to_mapping(f["fields"])
        f.pop("fields", None)
        return f
    elif isinstance(f, list):
        return { ai["name"]:conv_fields_to_mapping(pop_name(ai.copy())) for ai in f if "name" in ai }
    else:
        return f

def pop_name(a):
    if "name" in a:
        a.pop("name")
    return a

    

# arg parsing
parser = argparse.ArgumentParser(description='Run tooling related to elastic templaes .')
parser.add_argument('-a', '--action', type=str, required=True, dest='action', help="Action to run. 'show' will print the final template to stdout.", choices=[ "show" ], default="show")
parser.add_argument('-p', '--pipeline', type=str, required=True, dest='pipeline', help="Path to pipeline conf to run against. Should be relative to the projects root folder.")

argvars = vars( parser.parse_args() )

print("Called with arguments: %s" % argvars)

root_dir = os.path.abspath(sys.path[0]+'/../') +"/"

print(root_dir)

fields = {}
with open(  root_dir+"/doc/fields.yml", 'r') as ecs_fields_yml:
    fields = yaml.load(ecs_fields_yml)[0]["fields"]
#data = urllib.request.urlopen('https://raw.githubusercontent.com/elastic/ecs/master/fields.yml').read()
#fields = yaml.load(data)[0]["fields"]
for path in sorted(glob.glob(root_dir+"doc/avm-schemas/*.yml")):
    with open(path) as f:
        fields = fields + yaml.load(f.read())

prune_fields(fields, "")
expanded = expand_reusable_fields(fields)
mapping = conv_fields_to_mapping(expanded)
#print (  mapping  )
#print()
#print()
with open(  root_dir+"/doc/ecs-extension.yml", 'r') as f_extension:
    extension = yaml.load(f_extension)
extension = conv_fields_to_mapping(extension)    
#print( extension )
#print()
#print()
extension["properties"].update(mapping)
base = extension["properties"]["base"]
extension["properties"].pop("base", None)
extension["properties"].update(base["properties"])
print( json.dumps(extension, indent=4, sort_keys=True) )

#   {  
#      'name':'user',
#      'reusable':{  
#         'top_level':True,
#         'expected':[  
#            'destination',
#            'host',
#            'source'
#         ]
#      },
#      'type':'group',
#      'fields':[  
#         {  
#            'name':'id',
#            'type':'keyword'
#         },
#         {  
#            'name':'name',
#            'type':'keyword'
#         },
#         ...



