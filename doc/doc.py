import yaml
import csv
import argparse
import copy

import glob

import re
import os
import re
import json 
import sys
import urllib.request
from functools import reduce

# root_dir is the directory of the git repo elop-logstash-pipelines
root_dir = os.path.abspath(sys.path[0]+'/../') +"/"

#list all pipeline names according to the pattern pipelines/<beat>/<conf-filename-without-extension> - e.g. pipelines/filebeat/fail2ban-legacy
avm_pipelines = [ m[len(root_dir):-5] for m in glob.glob(root_dir+"pipelines/*/*.conf") if not os.path.isdir(m) ]


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



def get_markdown_section(namespace):
    namespace.pop('reusable', None)
    
    # Table
#    titles = ['Field']+['<details><summary>'+'['+str(i)+'](# "'+f+'")'+'</summary>'+f.replace('/',' / ')+'</details>' for i, f in enumerate(avm_pipelines)]
#    if section_name == "base":
#        for title in titles:
#           output += "| {}  ".format(title)
#        output += "|\n"
#        for title in titles:
#           output += "|---"
#        output += "|\n"


    #output = '<tr><th align="center" colspan='+str(len(avm_pipelines)+1)+'><h3>'+str(namespace["name"])+'</h2></td></tr>'
    output = '<tr><th rowspan=2><span title="'+namespace["description"]+'"><h4>'+str(namespace["name"])+'</h4></span></th>'+''.join(['<td colspan='+str(beats[k])+' align="center">'+str(k)+'</td>' for k in sorted(beats.keys())])+'</tr>'
    output += '<tr>'+''.join(['<td align="center"><span title="'+k+'">'+os.path.basename(k)[:2]+'</span></td>' for k in avm_pipelines])+'</tr>'

    for field in sorted(namespace["fields"], key=lambda field: field["name"]):
        output += get_markdown_row(field)


#    for field in orphans["fields"]:
#        output += get_markdown_row(field)

#    for field in [f for f in list(avm_must.keys()) if f not in second]  namespace["fields"]:
#        output += get_markdown_row(field, link, False)

    # output += "\n\n"

    # Footnote
    # if "footnote" in namespace:
    #    output += namespace["footnote"].replace("\n", "\n\n") + "\n"

    return output


def tr_bad_chars(s):
    return s.replace('"','').replace('[','').replace(']','').replace("\n", "   ")

def get_markdown_row(field):
    """Creates a markdown table for the given fields
    """

    # Replace newlines with HTML representation as otherwise newlines don't work in Markdown
    description = field["description"].replace("\n", "<\br>").replace('"','').replace('[','').replace(']','')

    if "example" in field:
        show_name = '<span title="'+'('+field["type"]+') '+tr_bad_chars(field["description"])+'    EXAMPLE: '+tr_bad_chars(field["example"])+'">'+field["name"]+'</span>'
        #show_name = '['+field["name"]+'](https://github.com/elastic/ecs "'+tr_bad_chars(field["description"])+'   EXAMPLE: '+tr_bad_chars(field["example"])+'")'+' ('+field["type"]+')'
    else:
        show_name = '<span title="'+'('+field["type"]+') '+tr_bad_chars(field["description"])+'">'+field["name"]+'</span>'
    #show_name = '<span title="('+field["type"]+')">'+field["name"]+'</span>'
        #show_name = '['+field["name"]+'](https://github.com/elastic/ecs "'+tr_bad_chars(field["description"])+'")'+' ('+field["type"]+')'

    #show_name.replace("\n", "<\br>").replace('"','').replace('[','').replace(']','')

    # If link is true, it link to the anchor is provided. This is used for the use-cases
    #if link and ecs:
        #str_pattern = '| [{}]({}#{})  |'+''.join([' {} |']*len(avm_pipelines))+' {} | {} | {} | {} |\n'

    # By default a anchor is attached to the name
    #str_pattern = '| <a name="{}"></a>{} |'+''.join([' {} |']*len(avm_pipelines))+' {} | {} | {} |\n'
    #str_pattern = '| <a name="{}"></a>{} |'+''.join([' {} |']*len(avm_pipelines))+'\n'
    #str_pattern = '<tr><td><a name="{}"></a>{}</td>'+''.join(['<td> {} </td>']*len(avm_pipelines))+'</tr>\n'
    str_pattern = '<tr><td>{}</td>'+''.join(['<td align="center"><b>{}</font></b>']*len(avm_pipelines))+'</tr>\n'
    #return str_pattern.format(field["name"], show_name, *[avm_must[f][field["name"]] if field["name"] in avm_must[f] else "" for f in avm_pipelines], description)
    #avm_must[f][field["name"]]
    #'[X](# "'+avm_must[f][field["name"]]+'")'
    #return str_pattern.format(field["name"], show_name, *['[X](# "'+f+': '+avm_must[f][field["name"]]+'")' if field["name"] in avm_must[f] else "CONT" for f in avm_pipelines])
    #return str_pattern.format(field["name"], show_name, *['[X](# "'+f+': '+str(avm_must[f][field["name"]])+'")' if field["name"] in avm_must[f] else "" for f in avm_pipelines])
    return str_pattern.format(show_name, *['<span title="'+f+': '+str(avm_must[f][field["name"]])+'">X</span>' if field["name"] in avm_must[f] else "" for f in avm_pipelines])



def create_csv(fields, file):

    open_mode = "wb"
    if sys.version_info >= (3, 0):
        open_mode = "w"

    # Output schema to csv
    with open(file, open_mode) as csvfile:
        schema_writer = csv.writer(csvfile,
                                   delimiter=',',
                                   quoting=csv.QUOTE_MINIMAL,
                                   lineterminator='\n')
        schema_writer.writerow(["Field", "Type", "Level", "Example"])

        for namespace in fields:
            if len(namespace["fields"]) == 0:
                continue

            # Sort fields for easier readability
            namespaceFields = sorted(namespace["fields"],
                                     key=lambda field: field["name"])

            # Print fields into a table
            for field in namespaceFields:
                schema_writer.writerow([field["name"], field["type"], field["level"], field["example"]])




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



#def filtered_fields(fields, groups):
#    new_fields = copy.deepcopy(fields)
#    for f in new_fields:
#        n = 0
#        for field in list(f["fields"]):
#            if field["group"] not in groups:
#                del f["fields"][n]
#                continue
#            n = n + 1
#
#    return new_fields


if __name__ == "__main__":
    #print ("GIT ROOT DIR: "+root_dir)
    #p = re.compile('.*?\%\{[^\}]*?:(.*?)\}+.*?')
    #p_example = re.compile('^#(?i)#[ ]*example:[ ]*(.*)$')
    #avm_examples = {}
    avm_must = {}
    for f in avm_pipelines:
    #    avm_examples[f] = []
        avm_must[f] = []
    #    for json_path in sorted( glob.glob(root_dir+'testing/'+f+"_"+EXAMPLE_JSON_IDENTIFIER+"must.json") ):
        for json_path in sorted( glob.glob(root_dir+'testing/'+f+"_*must.json") ):
            with open(  json_path, 'r') as must_file:
                avm_must[f] = flatten_json( json.load(must_file) )
            break
    # parse fields from the *.conf file
    #    for line in open(root_dir+f+'.conf', 'r').readlines():
    #        avm_must[f] = avm_must[f]+[ma.group(1).replace('][','.').replace('[','').replace(']','') for ma in p.finditer(line)]
    #        avm_examples[f] = avm_examples[f]+[ma.group(1) for ma in p_example.finditer(line)]


    #print ( avm_must )


    fields = []
    data = urllib.request.urlopen('https://raw.githubusercontent.com/elastic/ecs/master/fields.yml').read()
    fields = yaml.load(data)[0]["fields"]    
    for path in sorted(glob.glob(root_dir+"doc/avm-schemas/*.yml")):
        with open(path) as f:
            fields = fields + yaml.load(f.read())

    clean_namespace_fields(fields)
    
    # Load all fields into object
    sortedNamespaces = sorted(fields, key=lambda field: field["group"])
    #print (sortedNamespaces)

    fieldnames_flat = [i["name"] for l in sortedNamespaces for i in l["fields"]]
    avmmust_flat = list(set([f for k in list(avm_must.keys()) for f in avm_must[k] ]))
    orphaned = [f for f in avmmust_flat if f not in fieldnames_flat ]
    orphaned = {"name":"orphaned", "description":"Fields which are neither in the ecs nor in the avm schemas.", "fields":[{"name":f, "type":"", "description":""} for f in avmmust_flat if f not in fieldnames_flat ] }

    #print ( sortedNamespaces )
    #print ( fieldnames_flat )
    #print()
    #print ( orphaned )
    sortedNamespaces.append(orphaned)
    
    # Create markdown schema output string
    output = ""
    
    avm_pipelines.sort()
    beats = {}
    for beat in [os.path.basename(os.path.dirname(f)) for f in avm_pipelines]:
        beats[beat] = beats.get(beat, 0) + 1

    output = '<table>'    
    #output += '<thead>'
#    output += '<tr><th rowspan=2>Field</th>'+''.join(['<th colspan='+str(beats[k])+'>'+str(k)+'</th>' for k in sorted(beats.keys())])+'</tr>'
#    output += '<tr>'+''.join(['<th><span title="'+k+'">'+os.path.basename(k)[:1]+'</span></th>' for k in avm_pipelines])+'</tr>'
#    output += "</thead><tbody>"
    output += '<tbody>'
    for namespace in sortedNamespaces:
        #print( namespace["name"] )
        if len(namespace["fields"]) == 0:
            continue
        output += get_markdown_section(namespace)

    output += "</tbody></table>"
    print( output + "\n\n" )


    # Generates Markdown for README
#    if args.stdout == "true":

    # md out 
    #groups = [1, 2, 3]
    #f_fields = filtered_fields(sortedNamespaces, groups)
    # Print to stdout
    #print(create_markdown_document(f_fields))
    

    # Generates schema.csv
#    else:

    # csv out
#    groups = [1, 2, 3]
#    f_fields = filtered_fields(sortedNamespaces, groups)
#    create_csv(f_fields, "schema.csv")
