# TODO: comparison of base fields e.g. with avm_must root
# TODO: README.md: display orphans (separately)
# TODO: deep merge of avm-fields OR prohibit types in extension.yml
# TODO: improve details of error message in case of missing type field
import argparse
import os
import sys
import yaml 
import glob 
import json
import re

# root_dir is the directory of the git repo elop-logstash-pipelines
root_dir = os.path.abspath(sys.path[0]+'/../') +"/"
#print("\nroot directory: "+root_dir+"\n")
# arg parsing
parser = argparse.ArgumentParser(description='Run tooling related to elastic templaes .')
parser.add_argument('-a', '--action', type=str, required=True, dest='action', help="Action to run. 'show' will print the final template to stdout.", choices=[ "show", "doc" ], default="show")
parser.add_argument('-p', '--pipelines', type=str, required=True, dest='pipelines', help="Path to pipeline confs to run against. Should be relative to the projects root folder.")
#parser.add_argument('-p', '--pipelines', type=str, nargs='+', required=True, dest='pipelines', help="Paths to pipeline confs to run against. Should be relative to the projects root folder.")

argvars = vars( parser.parse_args() )

#print("Called with arguments: %s" % argvars)
#print(root_dir)
#print(argvars["pipeline"])

###################################################################################
# TRASH - functions from ecs repo - TRASH
###################################################################################

def clean_namespace_fields(fields):
    """Cleans up all fields to set defaults
    """
    for namespace in fields:

        # For now set the default group to 2
        if "group" not in namespace:
            namespace["group"] = 2

        prefix = ""
        # Prefix if not base namespace
        if namespace["name"] != "base":
            prefix = namespace["name"]

        if "fields" in namespace:
            clean_fields(namespace["fields"], prefix, namespace["group"])


def clean_fields(fields, prefix, group):
    for field in fields:
        clean_string_field(field, "description")
        clean_string_field(field, "footnote")
        clean_string_field(field, "example")
        clean_string_field(field, "type")

        # Add prefix if needed
        if prefix != "":
            field["name"] = prefix + "." + field["name"]

        if 'level' not in field.keys():
            field["level"] = '(use case)'

        if 'group' not in field.keys():
            # If no group set, set parent group
            field["group"] = group

        if "multi_fields" in field:
            for f in field["multi_fields"]:
                clean_string_field(f, "description")
                clean_string_field(f, "example")
                clean_string_field(f, "type")

                # multi fields always have a prefix
                f["name"] = field["name"] + "." + f["name"]

                if 'group' not in f.keys():
                    # If no group set, set parent group
                    f["group"] = group

def clean_string_field(field, key):
    """Cleans a string field and creates an empty string for the field in case it does not exist
    """
    if key in field.keys():
        # Remove all spaces and newlines from beginning and end
        field[key] = str(field[key]).strip()
    else:
        field[key] = ""


###################################################################################
# utils
###################################################################################

# removes comments from must files as well as pipeline conf files
comment_pattern = re.compile(r"^((((?<![\\])['\"])(?:.(?!(?<![\\])\3))*.?\3|[A-Za-z0-9,.: \t=>}{\[\]]*)+)(\#.*)?$")
def withdraw_comments(json_lines):
    resJson = ""
    # Filter comments - through quote matching by means of lookbehind: +((?<![\\])['"])((?:.(?!(?<![\\])\2))*.?)\2
    for line in json_lines:
        res = comment_pattern.match(line)
        if res:
            resJson += res.group(1)
        else:
            resJson += line
    return resJson


# flattens nested dict structures - designated for must files and testoutput
def flatten_json(y):
    out = {}
    def flatten(x, name=''):
        if type(x) is dict:
            for a in x:
                flatten(x[a], name + a + '.')
        else:
            out[name[:-1]] = x
    flatten(y)
    return out


# updates nested dict recusively (array are overridden)
def deep_update(d, inset, conflict_action):
    def deep_update(d, inset, conflict_action, str_path):
        for k in inset.keys():
            if not k in d: 
                d.update({k:inset[k]})
            else:
                if isinstance(inset[k], dict):
                    deep_update(d[k], inset[k], conflict_action, str_path+"."+k if str_path else k)
#                if isinstance(inset[k], list) and isinstance(d[k], list):
#                => fortunately not necessary
                else:
                    if d[k] != inset[k] and conflict_action:
                        if conflict_action == "override":
                            d[k] = inset[k]
                        elif conflict_action == "error":
                            raise Exception( "error: found conflict: unable to override '"+str_path+"."+k+"':  "+str(inset[k])+" => "+str(d[k]) )

    deep_update(d, inset, conflict_action, "")


# converts nested field arrays to index mapping dicts
def conv_fields_to_dict(o):
    def pop_name(a):
        if "name" in a:
            a.pop("name")
        return a

    def namesplit(arr, o):
        if len(arr) > 1:
            return {arr[0]:{"properties": namesplit(arr[1:],o)}}
        elif len(arr) == 1:
            return {arr[0]:o}
        return {}
    
    f = o.copy()
    if isinstance(f, dict) and "fields" in f:
        f["properties"] = conv_fields_to_dict(f["fields"])
        f.pop("fields", None)
        return f
    elif isinstance(f, list):
        #return { k["name"]:conv_fields_to_dict(pop_name(k.copy())) for k in f if "name" in k }
        result = {}
        for k in f:
            if "name" in k:
                deep_update(result, namesplit( k["name"].split("."), conv_fields_to_dict(pop_name(k.copy())) ), conflict_action="error")
            
        return result
    else:
        return f


# helper class for navigation in mapping-related structures
class Mapping:
    def __init__(self, mapping):
        self.mapping = mapping
        self.nav = self._get_mapping_nav(mapping, []) # e.g. 'http.response'=>['http','response']

    # a nav is a dict of type {string: list}, e.g. {'http.response': ['http','response'], ...}
    def _get_mapping_nav(self, m,prefix):
        result = {}
        if isinstance(m, dict) and "type" in m:
            result.update( {".".join(prefix):prefix} )
        if isinstance(m, dict) and "properties" in m:
            result.update( { k2:v2 for (k,v) in m["properties"].items() for (k2,v2) in self._get_mapping_nav(v, prefix+[k]).items() } )
        if isinstance(m, dict) and "fields" in m:
            result.update( { k2:v2 for (k,v) in m["fields"].items() for (k2,v2) in self._get_mapping_nav(v, prefix+[k]).items() } )
        return result

    # gathers all settings of a given path - on every depth of the path
    def accumulate(self, path):
        def accumulate(mapping, path):
            result = {}
            result.update( {k:v for (k,v) in mapping.items() if k!="properties" and k!="fields" } )
            
            if path != []:
                if "properties" in mapping and path[0] in mapping["properties"]:
                    result.update( {"properties": {path[0]: accumulate(mapping["properties"][path[0]], path[1:])} } )

                if "fields" in mapping and path[0] in mapping["fields"]:
                    result.update( {"fields": accumulate(mapping["properties"][path[0]], path[1:]) } )

            return result
        
        #if isinstance(path, str) and path in self.nav:
        #    return accumulate(self.mapping, self.nav[path])
        #if isinstance(path, list):
        #    return accumulate(self.mapping, path)
        #return {}
        return accumulate(self.mapping, path)

    # navigates to a specific path and returns the resulting dict
    def navigate(self, path):
        def navigate(mapping, path):
            result = {}
            if path == []:
                result.update( {k:v for (k,v) in mapping.items() if k!="properties" and k!="fields" } )
            
            if path != []:
                if "properties" in mapping and path[0] in mapping["properties"]:
                    return navigate(mapping["properties"][path[0]], path[1:])

                if "fields" in mapping and path[0] in mapping["fields"]:
                    return navigate(mapping["fields"][path[0]], path[1:])

            return result
        
        if isinstance(path, str) and path in self.nav:
            return navigate(self.mapping, self.nav[path])
        if isinstance(path, list):
            return navigate(self.mapping, path)
        return {}
        #return navigate(self.mapping, path)

    # partitions all path strings by first field
    def get_all_keys_partitioned_by_namespace(self):
        result = {}
        for k, v in self.nav.items():
            result[v[0]] = result.get(v[0], [])
            result[v[0]].append(k)
        
        return result

    def collate_mapping(self, paths):
        paths.sort()
        result = {}
        for i in paths:
            if i in self.nav:
                print ("# found: " + i + "   " + str(self.nav[i]))
                deep_update(result, self.accumulate(self.nav[i]), conflict_action=None)
            else:
                print ("# WARNING: ignoring orphaned field which was not found in the avm/ecs schema: " + i)
        return result

    def collate_template(self, paths):
        result = self.collate_mapping(paths)
        return {"mappings":{"_doc":result}}

    def print(self):
        print( json.dumps(self.mapping, indent=4, sort_keys=True) )


###################################################################################
# load data
###################################################################################

# expands reusable fields at places expected (as designated by reusable property)
def expand_ecs_fields_to_mapping(f):
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
    result = [{k:v for (k,v) in d.items() if not k=="reusable"} for d in root if not "reusable" in d or ("top_level" in d["reusable"] and d["reusable"]["top_level"]==True)]
    result = conv_fields_to_dict(result)

    if argvars["action"] == "show":
        base = result["base"]
        result.pop("base", None)
        result.update(base["properties"])
    
    return result


def prune_ecs_fields(f, assert_type_field_exists):
    def assert_key_existence(key):
        if key in f.keys():
            f[key] = str(f[key]).strip() # Remove leading/trailing spaces and newlines 
        else:
            raise Exception("key " + key + " does not exist")
    
    if argvars["action"] == "doc":
        #list_keys_to_remove=["footnote","required"]
        list_keys_to_remove=[]
    if argvars["action"] == "show":    
        list_keys_to_remove=["title","description","footnote","example","level","group","required"]
    
    if isinstance(f, dict):
        for kpr in list_keys_to_remove:
            f.pop(kpr, None)
        assert_key_existence("name")
        if "multi_fields" in f:
            prune_ecs_fields(f["multi_fields"], assert_type_field_exists)
        if "fields" in f and isinstance(f["fields"], list):
            f.pop("type", None)
            prune_ecs_fields(f["fields"], assert_type_field_exists)
        elif assert_type_field_exists:
            assert_key_existence("type")
    elif isinstance(f, list):
        for g in f:
            prune_ecs_fields(g, assert_type_field_exists)

fields = []
with open(  root_dir+"/doc/fields.yml", 'r') as ecs_fields_yml:
    fields = yaml.load(ecs_fields_yml)[0]["fields"]

for path in sorted(glob.glob(root_dir+"doc/avm-schemas/*.yml")):
    with open(path, 'r') as f:
        avmyml = yaml.load(f.read())
        if "fields" in avmyml:
            fields = fields + avmyml["fields"]
        else:
            raise Exception("ERROR: missing keyword 'field:' in yaml file: " + path)

#print (  fields )
prune_ecs_fields(fields, assert_type_field_exists=True)
m_expanded = expand_ecs_fields_to_mapping(fields)
#print (  m_expanded  )
#print()
#print()
with open(  root_dir+"/doc/ecs-extension.yml", 'r') as f_extension:
    extension = yaml.load(f_extension)

#print( extension )

prune_ecs_fields(extension["fields"], assert_type_field_exists=False)
m_extension = conv_fields_to_dict(extension)    
#print( m_extension )
#exit()
#print()
#print()
deep_update(m_extension["properties"], m_expanded, conflict_action="error")

mapping = Mapping(m_extension)

#mtest = Mapping(m_expanded)
#mtest.print()
#mapping.print()
#print()
#print()
#exit()


###################################################################################
# doc generation
###################################################################################

if argvars["action"] == "doc":
    def tr_bad_chars(s):
        return str(s).replace('"','').replace('[','').replace(']','').replace("\n", "   ")
    
    avm_pipelines = [ m[len(root_dir):-5] for m in glob.glob(root_dir+"pipelines/*/*.conf") if os.path.isfile(m) and m[-5:]==".conf" ]
    avm_pipelines.sort()
    
    avm_must = {}
    for p in avm_pipelines:
        avm_must[p] = {}
        for json_path in sorted( glob.glob(root_dir+'testing/'+p+"_*_must.json") ):
            with open(  json_path, 'r') as must_file:
                avm_must[p].update( flatten_json(  json.loads( withdraw_comments(must_file) )  ) )
    
    avmmust_flat = list(set([a for p in list(avm_must.keys()) for a in avm_must[p]]))
    #mapping.nav
    #orphaned = [{"name":f, "type":"", "description":""} for f in avmmust_flat if f not in mapping.nav ]
    #print (orphaned)

    avm_pipelines.sort()
    beats = {}
    for beat in [os.path.basename(os.path.dirname(f)) for f in avm_pipelines]:
        beats[beat] = beats.get(beat, 0) + 1

    output = '<table><tbody>'
    ns_key_map = mapping.get_all_keys_partitioned_by_namespace() # fieldpaths partitioned by namespace
    for ns in sorted( list(ns_key_map.keys()) ):
        output += '<tr><th rowspan=2><span title="'+mapping.navigate(ns).get("description", "")+'"><h4>'+str(ns)+'</h4></span></th>'+''.join(['<td colspan='+str(beats[b])+' align="center">'+str(b)+'</td>' for b in sorted(beats.keys())])+'</tr>'
        output += '<tr>'+''.join(['<td align="center"><span title="'+p+'">'+os.path.basename(p)[:2]+'</span></td>' for p in avm_pipelines])+'</tr>'

        #for field in sorted(namespace["fields"], key=lambda field: field["name"]):
        for path in sorted(ns_key_map[ns]):
            field = mapping.navigate(path)
            #def get_markdown_row(path, field):
            #path = ".".join(path)
            # Replace newlines with HTML representation as otherwise newlines don't work in Markdown
            description = field["description"].replace("\n", "<\br>").replace('"','').replace('[','').replace(']','')
            
            if "example" in field:
                show_name = '<span title="'+'('+field["type"]+') '+tr_bad_chars(field["description"])+'    EXAMPLE: '+tr_bad_chars(str(field.get("example","")))+'">'+path+'</span>'
            else:
                show_name = '<span title="'+'('+field["type"]+') '+tr_bad_chars(field["description"])+'">'+path+'</span>'

            str_pattern = '<tr><td>{}</td>'+''.join(['<td align="center"><b>{}</font></b>']*len(avm_pipelines))+'</tr>\n'
            output += str_pattern.format(show_name, *['<span title="'+f+': '+str(avm_must[f][path])+'">X</span>' if path in avm_must[f] else "" for f in avm_pipelines])
    output += "</tbody></table>"
    with open(root_dir+"README.md", "w") as readme:
        with open(root_dir+"INTRO.md", "r") as intro:
            readme.write(intro.read() + "\n\n## Felder\n")
        readme.write(output + "\n\n")
    
    print( "Die README-Datei wurde aktualisiert.\n" )


###################################################################################
# mapping generation
###################################################################################

if argvars["action"] == "show":
    avm_pipelines = [ m[len(root_dir):-5] for p in argvars["pipelines"].split(",") for m in glob.glob(root_dir+p) if os.path.isfile(m) and m[-5:]==".conf" ]
    avm_pipelines.sort()

    avm_must = {}
    for p in avm_pipelines:
        avm_must[p] = {}
        for json_path in sorted( glob.glob(root_dir+'testing/'+p+"_*_must.json") ):
            with open(  json_path, 'r') as must_file:
                avm_must[p].update( flatten_json(  json.loads( withdraw_comments(must_file) )  ) )
        
        print ()
        print ("# Pipeline: "+p+".conf")
        print ("#")
        avmmust_flat = list(set([a for a in avm_must[p]]))
        #result = mapping.collate_mapping(avmmust_flat)
        result = mapping.collate_template(avmmust_flat)
        
        if os.path.isfile( root_dir+p+"-template.json" ):
            with open(root_dir+p+"-template.json", 'r') as f_template:
                template = json.loads( withdraw_comments(f_template) )
        else:
            with open(root_dir+"standard-template.json", 'r') as f_template:
                template = json.loads( withdraw_comments(f_template) )
                template.update({"index_patterns": [ os.path.basename(root_dir+p+".conf")[:-5]+"*" ]}),
        deep_update(template, result, conflict_action="error")
        
        print( json.dumps(template, indent=4, sort_keys=True) )
        print ()
        

    #avmmust_flat = list(set([p for k in list(avm_must.keys()) for p in avm_must[k] ])) 


