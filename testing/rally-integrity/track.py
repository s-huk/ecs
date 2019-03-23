import sys
import os
root_dir2 = os.path.abspath('../../')+"/"
#print ("root_dir2: " + root_dir2)
sys.path.append(root_dir2+"src")
import genutil

def create_indices_and_insert_data(es, params):
    print ("\nroot_dir2: " + root_dir2)
    genutil.submit_templates(es, "test-template")
    #pass
    

#def outsearch(es, params):
#    print ("\n")
#    res = es.search(
#        index=params["index"],
#        body=params["body"]
#    )
#    for hit in res["hits"]["hits"]:
#        print(str(hit)+"\n")
#def filldata(es, params):
#    print ("\n")
#    res = es.index(
#        index=params["index"],
#        body=params["body"]
#    )
#    for json_path in sorted( glob.glob('pipelines/*/*_must.json') ):
#        with open(  json_path, 'r') as must_json:
#            print("# INSERT DOCUMENT: "+json_path)
#            es.index( index="bla", body=json.loads(withdraw_comments(must_file)) )

def register(registry):
    registry.register_runner("optype_create_indices_and_insert_data", create_indices_and_insert_data)
#    registry.register_runner("outsearch", outsearch)
#    registry.register_runner("filldata", filldata)
