import os, sys
try:                                            # if running in CLI
    cur_path = os.path.abspath(__file__)
except NameError:                               # if running in IDE
    cur_path = os.getcwd()

while cur_path.split('/')[-1] != 'research_match':
    cur_path = os.path.abspath(os.path.join(cur_path, os.pardir))    
sys.path.insert(1, os.path.join(cur_path, 'lib', 'python3.7', 'site-packages'))

import _connections
import pandas as pd
import numpy as np
from pg_tables import create_tables

mongo = _connections.db_connection('mongo')
psql = _connections.db_connection('psql')


def pg_insert(cur, script):
    try:
        cur.execute(script)
        cur.execute("commit;")
        
    except Exception as e:
        print("Error: {}".format(str(e)))
        raise(Exception)
        
    
def pg_query(cur, query):
    cur.execute(query)
    data = pd.DataFrame(cur.fetchall())
    return(data) 
    
def pg_create_table(cur, table_name):  
#    cur, table_name = _psql, 
    try:
        # Truncate the table first
        for script in create_tables[table_name]:
            cur.execute(script)
            cur.execute("commit;")
        print("Created {}".format(table_name))
        
    except Exception as e:
        print("Error: {}".format(str(e)))

def _det_current_pubs(_psql):
#    _psql = psql.client
    try:
        pub_data = pg_query(_psql.client, 'select pub_id, name from research_match.publishers;')
    except:
        _psql.reset_db_con()
        pg_create_table(_psql.client, 'publishers')
        pub_data = pg_query(_psql.client, 'select pub_id, name from research_match.publishers;')
    if len(pub_data) > 0:
        current_publishers = set(pub_data[1].values)
        next_pub_idx = np.max(pub_data[0]) + 1
    else:
        next_pub_idx = 0
        current_publishers = set([])
    return(next_pub_idx, current_publishers, _psql)

def _det_current_auths(_psql):
    try:
        auth_data = pg_query(_psql, 'select auth_id, name from research_match.authors;')
    except:
        _psql.reset_db_con()
        pg_create_table(_psql.client, 'authors')
        auth_data = pg_query(_psql, 'select auth_id, name from research_match.authors;')
    
    if len(auth_data) > 0:
        current_authors = set(auth_data[1].values)
        next_auth_idx = np.max(auth_data[0]) + 1
    else:
        next_auth_idx = 0
        current_authors = set([])
    return(next_auth_idx, current_authors)


nxt_pub, cur_pubs, psql = _det_current_pubs(psql)
for entry in mongo.client.find():
    if 'abstract' not in entry.keys():
        continue
    if 'publisher' in entry.keys():
        if entry['publisher']['name'] not in cur_pubs:
            pg_insert(psql.client, "insert into research_match.publishers (pub_id, name, page) VALUES (%i, '%s', '%s')" % (nxt_pub, entry['publisher']['name'], entry['publisher']['page']))
            cur_pubs.add(entry['publisher']['name'])
            nxt_pub += 1
            
nxt_auth, cur_auths, psql = _det_current_auths(psql)
for entry in mongo.find():
    if 'abstract' not in entry.keys():
        continue
    if 'authors' in entry.keys():
        for auth in entry['authors']:
            if auth['name'] not in cur_auths:
                if 'page' not in auth.keys():
                    auth['page'] = "NULL"
                script = "insert into research_match.authors (auth_id, name, page) VALUES (%i, '%s', '%s')" % (nxt_auth, auth['name'], auth['page'])
                script = script.replace("'NULL'", 'NULL')
                pg_insert(psql.client, script)
                cur_auths.add(auth['name'])
                nxt_auth += 1                
        

