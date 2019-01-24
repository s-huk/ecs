# OK: comparison of base fields e.g. with avm_must root
# OK: README.md: display orphans (separately)
# OK: deep merge of avm-fields OR prohibit types in extension.yml
# OK: merge existing json template properties
# OK: improve details of error message in case of missing type field
# TODO: re-think acceptance of type-less fields
# OK: console output doc of pipeline singletons
# OK: check if template props override yml props
import argparse
import os
import sys
import yaml 
import glob 
import json
import re
import getpass
#from elasticsearch import Elasticsearch
#import certifi
import requests

# root_dir is the directory of the git repo elop-logstash-pipelines
root_dir = os.path.abspath(sys.path[0]+'/../') +"/"
#print("\nroot directory: "+root_dir+"\n")
# arg parsing
parser = argparse.ArgumentParser(description='Run tooling related to elastic templaes .')
parser.add_argument('-a', '--action', type=str, required=False, dest='action', help="Action to run. 'show' will print the final template to stdout.", choices=[ "show", "gen-doc", "submit-template" ], default="show")
parser.add_argument('-p', '--pipelines', type=str, required=False, dest='pipelines', help="Path to pipeline confs to run against. Should be relative to the projects root folder.", default="pipelines/*/*.conf")
parser.add_argument('-c', '--cluster', type=str, required=False, dest='cluster', help="Target cluster to set the template on. Example: 'http://172.16.78.100:9200'")

#parser.add_argument('-p', '--pipelines', type=str, nargs='+', required=True, dest='pipelines', help="Paths to pipeline confs to run against. Should be relative to the projects root folder.")

argvars = vars( parser.parse_args() )

if argvars["action"] == "submit-template" and argvars["cluster"] is None:
    parser.error("--pipelines submit-template requires --cluster")

print()


# stdout selected pipelines
if argvars["action"] == "gen-doc" and argvars["pipelines"] != "pipelines/*/*.conf":
    print("ignoring argument -p " + argvars["pipelines"])
    argvars["pipelines"] = "pipelines/*/*.conf"
    
avm_pipelines = [ m[len(root_dir):-5] for p in argvars["pipelines"].split(",") for m in glob.glob(root_dir+p) if os.path.isfile(m) and m[-5:]==".conf" ]
avm_pipelines.sort()
print (" => "+"\n => ".join(avm_pipelines))


#print("Called with arguments: %s" % argvars)
#print(root_dir)
#print( str(argvars) )
#exit()

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
                            print ( "# WARNING: value overridden: '"+str_path+"."+k+"':  "+str(inset[k])+" => "+str(d[k]) )
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

    def path_exists(self, path):
        def path_exists(path, mapping):
            if path != []:
                for fieldkey in ["properties", "fields"]:
                    if fieldkey in mapping and path[0] in mapping[fieldkey]:
                        return path_exists(path[1:], mapping[fieldkey][path[0]])
                return False
            return True
        return path_exists(path, self.mapping)

    def amend_path(self, path, error_non_existing):
        if isinstance(path, str):
            if path in self.nav:
                path = self.nav[path]
            else:
                path = path.split(".")
        if isinstance(path, list):
            if self.path_exists(path) == True:
                return path
            if self.path_exists(['base']+path) == True:
                return ['base']+path
            if error_non_existing:
                raise Exception("Path not found: " + str(path))
        
    # gathers all settings of a given path - on every depth of the path
    def accumulate(self, path):
        def ping(mapping, path):
            result = {k:v for (k,v) in mapping.items() if k!="properties" and k!="fields" }
            
            if path != []:
                for fieldkey in ["properties", "fields"]:
                    if fieldkey in mapping and path[0] in mapping[fieldkey]:
                        result.update( {fieldkey: pong(mapping[fieldkey], path)} )
                        return result
                return pong(mapping, path)
            
            return result
        
        def pong(mapping, path):
            if path[0] in mapping:
                return {path[0]: ping(mapping[path[0]], path[1:])}
#            elif path[0] in mapping.get('base', {"properties": None})["properties"]:
#                return {path[0]: ping(mapping["base"]["properties"][path[0]], path[1:])}
            raise Exception("Path not found: " + str(path) + "   " + str(mapping["properties"].keys()))
        
        return ping(self.mapping, self.amend_path(path, error_non_existing=True))

    
    # navigates to a specific path and returns the resulting dict
    def navigate(self, path):
        def ping(mapping, path):
            if path != []:
                for fieldkey in ["properties", "fields"]:
                    if fieldkey in mapping:
                        return pong(mapping[fieldkey], path)
                return pong(mapping, path)
            return mapping.copy()
        def pong(mapping, path):
            if path[0] in mapping:
                return ping(mapping[path[0]], path[1:])
            raise Exception("Path not found: " + str(path))
        
        return ping(self.mapping, self.amend_path(path, error_non_existing=True))


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
            p = self.amend_path(i, error_non_existing=False)
            if p:
                deep_update(result, self.accumulate(p), conflict_action=None)
#                print ("# found: " + i + "   " + str(p))                
#                #deep_update(result, self.accumulate(p), conflict_action="error")
#            else:
#                print ("# WARNING: ignoring orphaned field which was not found in the avm/ecs schema: " + i)

        # relocate 'base' to root
        if "properties" in result: 
            if "base" in result["properties"]:
                base = result["properties"].pop("base")
                deep_update(result, base, "error")
            
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

    return result


def strip_json_values(f):
    if isinstance(f, dict):
        for key in f.keys():
            if isinstance(f[key], str):
                f[key] = f[key].strip()
            else: 
                strip_json_values(f[key])
    elif isinstance(f, list):
        for g in f:
            strip_json_values(g)

def prune_ecs_fields(f, assert_type_field_exists):
    list_keys_to_remove=[]
    if argvars["action"] != "gen-doc":
        list_keys_to_remove=["title","description","footnote","example","level","group","required"]
    #elif: # doc, stat, etc.
    #    list_keys_to_remove=[] # ["footnote","required"]

    if isinstance(f, dict):
        for kpr in list_keys_to_remove:
            f.pop(kpr, None)
        if not "name" in f.keys():
            raise Exception("key 'name' does not exist in field: " + str(f))
        if "multi_fields" in f:
            prune_ecs_fields(f["multi_fields"], assert_type_field_exists)
        if "fields" in f and isinstance(f["fields"], list):
            f.pop("type", None)
            prune_ecs_fields(f["fields"], assert_type_field_exists)
        elif assert_type_field_exists and not "type" in f.keys():
            raise Exception("key 'type' does not exist in field: " + str(f))
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
strip_json_values(fields)
prune_ecs_fields(fields, assert_type_field_exists=True)
m_expanded = expand_ecs_fields_to_mapping(fields)
#print (  m_expanded  )
#print()
#print()
with open(  root_dir+"/doc/ecs-extension.yml", 'r') as f_extension:
    extension = yaml.load(f_extension)

#print( extension )

strip_json_values(extension)
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
#print( json.dumps(mapping.mapping, indent=3, sort_keys=True) )
#exit()


###################################################################################
# doc generation
###################################################################################

if argvars["action"] == "gen-doc":
    def tr_bad_chars(s):
        return str(s).replace('"','').replace('[','').replace(']','').replace("\n", "   ")
    
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

    beats = {}
    for beat in [os.path.basename(os.path.dirname(f)) for f in avm_pipelines]:
        beats[beat] = beats.get(beat, 0) + 1

    output = '<table><tbody>'
    ns_key_map = mapping.get_all_keys_partitioned_by_namespace() # fieldpaths partitioned by namespace
    nslist = sorted(  list(ns_key_map.keys())  )
    nslist.remove("base")
    nslist.remove("avm")
    #for ns in sorted( list(ns_key_map.keys()) ):
    for ns in ["base"] + nslist + ["avm"]:
        output += '<tr><th rowspan=2><span title="'+mapping.navigate(ns).get("description", "")+'"><h4>'+str(ns)+'</h4></span></th>'+''.join(['<td colspan='+str(beats[b])+' align="center">'+str(b)+'</td>' for b in sorted(beats.keys())])+'</tr>'
        output += '<tr>'+''.join(['<td align="center"><span title="'+p+'">'+os.path.basename(p)[:2]+'</span></td>' for p in avm_pipelines])+'</tr>'

        #for field in sorted(namespace["fields"], key=lambda field: field["name"]):
        for path in sorted(ns_key_map[ns]):
            field = mapping.navigate(path)
            
            if path.startswith("base."):
                path = path[5:]
            

            #def get_markdown_row(path, field):
            #path = ".".join(path)
            # Replace newlines with HTML representation as otherwise newlines don't work in Markdown
            description = str(field.get("description", "")).replace("\n", "<\br>").replace('"','').replace('[','').replace(']','')
            
            if "example" in field:
                show_name = '<span title="'+'('+field["type"]+') '+tr_bad_chars(field.get("description", ""))+'    EXAMPLE: '+tr_bad_chars(field.get("example",""))+'">'+path+'</span>'
            else:
                show_name = '<span title="'+'('+field["type"]+') '+tr_bad_chars(field.get("description", ""))+'">'+path+'</span>'

            str_pattern = '<tr><td>{}</td>'+''.join(['<td align="center"><b>{}</font></b>']*len(avm_pipelines))+'</tr>\n'
            output += str_pattern.format(show_name, *['<span title="'+f+': '+str(avm_must[f][path])+'">X</span>' if path in avm_must[f] else "" for f in avm_pipelines])
    
    # ORPHANED FIELDS
    output += '<tr><th rowspan=2><span title=""><h4>orphaned</h4></span></th>'+''.join(['<td colspan='+str(beats[b])+' align="center">'+str(b)+'</td>' for b in sorted(beats.keys())])+'</tr>'
    output += '<tr>'+''.join(['<td align="center"><span title="'+p+'">'+os.path.basename(p)[:2]+'</span></td>' for p in avm_pipelines])+'</tr>'
    
    for path in sorted(list(set([i for f in avm_pipelines for i in avm_must[f] if not mapping.amend_path(i, error_non_existing=False)]))):
        show_name = '<span title="()">'+path+'</span>'
        str_pattern = '<tr><td>{}</td>'+''.join(['<td align="center"><b>{}</font></b>']*len(avm_pipelines))+'</tr>\n'
        output += str_pattern.format(show_name, *['<span title="'+f+': '+str(avm_must[f][path])+'">X</span>' if path in avm_must[f] else "" for f in avm_pipelines])
    
    output += "</tbody></table>"
    with open(root_dir+"README.md", "w") as readme:
        with open(root_dir+"INTRO.md", "r") as intro:
            readme.write(intro.read() + "\n\n## Felder\n")
        readme.write(output + "\n\n")
    
    print( "\nDie README-Datei wurde aktualisiert.\n" )


###################################################################################
# mapping generation
###################################################################################

if argvars["action"] == "show" or argvars["action"] == "submit-template":
   
    if argvars["action"] == "submit-template":
        yes_no = input("\nSollen die oben stehenden Templates wirklich an den Server " + argvars["cluster"] + " geschickt werden? [y/N] ")
        if yes_no == '' or yes_no[0].lower().strip() != 'y':
            print("\nAktion wurde nicht durchgeführt.\n")
            exit()
#        user = input("\nServer-Benutzer: [] ")
#        if user == '' or user[0].lower().strip() == '':
#            print("\nKein Benutzername angegeben. Aktion abgebrochen.\n")
#        passwd = getpass.getpass("\nPasswort: ")
#        if passwd == '':
#            print("\nProbleme bei der Passworteingabe. Aktion abgebrochen.\n")
    
    avm_must = {}
    for p in avm_pipelines:
        avm_must[p] = {}
        for json_path in sorted( glob.glob(root_dir+'testing/'+p+"_*_must.json") ):
            with open(  json_path, 'r') as must_file:
                avm_must[p].update( flatten_json(  json.loads( withdraw_comments(must_file) )  ) )
        
        print ()
        print ("#############################################################")
        print ("# Pipeline: "+p+".conf")
        print ("#############################################################")
#        if argvars["action"] == "show": # console doc summary
        
        #
        # print schema
        #
        print ("#")
        beats = {os.path.basename(os.path.dirname(p)): 1}

        #output = os.path.basename(p)+'\n'
        output = ""
        ns_key_map = mapping.get_all_keys_partitioned_by_namespace() # fieldpaths partitioned by namespace
        nslist = sorted(  list(ns_key_map.keys())  )
        nslist.remove("base")
        nslist.remove("avm")
        #for ns in sorted( list(ns_key_map.keys()) ):
        for ns in ["base"] + nslist + ["avm"]:
            output += '#    '+str(ns)+'\n'

            for path in sorted(ns_key_map[ns]):
                field = mapping.navigate(path)
                
                if path.startswith("base."):
                    path = path[5:]
                
                # str(field.get("example",""))
                # str(field.get("description", ""))
                show_name = path +' ['+field["type"]+']'
                output += '#        '+show_name+': '+str(avm_must[p][path]) +'\n' if path in avm_must[p] else ""
                
        
        # ORPHANED FIELDS
        output += '#    orphaned'+'\n'
        for path in sorted(list(set([i for i in avm_must[p] if not mapping.amend_path(i, error_non_existing=False)]))):
            show_name = path +' [?]'
            output += '#        '+show_name+': '+str(avm_must[p][path]) +'\n' if path in avm_must[p] else ""
                
        print( output+"\n" )
        #
        # end: print schema
        #

        avmmust_flat = list(set([a for a in avm_must[p]]))
        #result = mapping.collate_mapping(avmmust_flat)
        result = mapping.collate_template(avmmust_flat)
        
        if os.path.isfile( root_dir+p+"-template.json" ):
            with open(root_dir+p+"-template.json", 'r') as f_template:
                template = json.loads( withdraw_comments(f_template) )
        else:
            with open(root_dir+"standard-template.json", 'r') as f_template:
                template = json.loads( withdraw_comments(f_template) )
                #template.update({"index_patterns": [ os.path.basename(root_dir+p+".conf")[:-5]+"*" ]}),
        
        #deep_update(template, result, conflict_action="error")
        deep_update(result, template, conflict_action="override")

        templateName = "genutil-prototest-"+p[10:].replace("/", "-")
        result.update({"index_patterns": [ templateName+"*" ]})
        
        print( json.dumps(result, indent=4, sort_keys=True) )
        print ()
        
        if argvars["action"] == "submit-template":
            resp = requests.put(argvars["cluster"]+'/_template/'+templateName, json=result)
            if resp.status_code == 200:
                print( "#    TEMPLATE AKTUALISIERUNG ERFOLGREICH: " + str(resp.content) )
            else:
                print("#    TEMPLATE AKTUALISIERUNG FEHLGESCHLAGEN: " + str(resp.content) )
    
    if argvars["action"] == "submit-template":
        print("\nAktion wurde durchgeführt.\n")
        
    #avmmust_flat = list(set([p for k in list(avm_must.keys()) for p in avm_must[k] ])) 


