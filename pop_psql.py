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
PSQL = _connections.db_connection('psql')


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

id_translate = {'institutions': 'inst', 'authors': 'auth', 'publishers': 'pub', 'papers': 'pap'}

def _det_current_(_psql, field):
#    _psql = psql.client
    try:
        _data = pg_query(_psql.client, 'select %s_id, page from research_match.%s;' % (id_translate[field], field))
    except:
        _psql.reset_db_con()
        pg_create_table(_psql.client, field)
        _data = pg_query(_psql.client, 'select %s_id, page from research_match.%s;' % (id_translate[field], field))
    if len(_data) > 0:
        current_ = set(_data[1].values)
        next_idx = np.max(_data[0]) + 1
    else:
        next_idx = 0
        current_ = set([])
    return(next_idx, current_, _psql)
        
def pop_pubs(psql):
    nxt_pub, cur_pubs, psql = _det_current_(psql, 'publishers')
    for entry in mongo.client.find({'abstract': {'$exists': True}, 'publisher': {'$exists': True}}):
        entry['publisher']['page'] = entry['publisher']['page'].replace('https://www.researchgate.net/', '').lower()
        if entry['publisher']['page'] not in cur_pubs:
            script = "insert into research_match.publishers (pub_id, name, page, page_hash) VALUES (%i, '%s', '%s', %i)" % (nxt_pub, entry['publisher']['name'].lower(), entry['publisher']['page'], hash(entry['publisher']['page']))
            pg_insert(psql.client, script)
            cur_pubs.add(entry['publisher']['page'])
            nxt_pub += 1
        
    
def pop_paps(psql):
    nxt_pap, cur_paps, psql = _det_current_(psql, 'papers')
    for entry in mongo.client.find({'abstract': {'$exists': True}}):
        entry['url_tag'] = entry['url_tag'].lower()
        if entry['url_tag'] not in cur_paps:
            script = "insert into research_match.papers (pap_id, mongo_hash, page, page_hash) VALUES (%i, '%s', '%s', %i)" % (nxt_pap, str(entry['_id']), entry['url_tag'], hash(entry['url_tag']))
            script = script.replace("'NULL'", 'NULL')
            pg_insert(psql.client, script)
            cur_paps.add(entry['url_tag'])
            nxt_pap += 1                

   
def pop_inst(psql):
    nxt_inst, cur_insts, psql = _det_current_(psql, 'institutions')
    for entry in mongo.client.find({'abstract': {'$exists': True}, 'authors': {'$exists': True}}):
        for auth in entry['authors']:
            if 'institution' in auth.keys():
                inst = auth['institution']
                if 'page' not in inst.keys():
                    continue   
                inst['page'] = inst['page'].replace('https://www.researchgate.net/', '').lower()
                if inst['page'] not in cur_insts:
                    script = "insert into research_match.institutions (inst_id, name, page, page_hash) VALUES (%i, '%s', '%s', %i)" % (nxt_inst, inst['name'].lower(), inst['page'], hash(inst['page']))
                    script = script.replace("'NULL'", 'NULL')
                    pg_insert(psql.client, script)
                    cur_insts.add(inst['page'])
                    nxt_inst += 1                


def pop_auth(psql):
    nxt_auth, cur_auths, psql = _det_current_(psql, 'authors')
    for entry in mongo.client.find({'abstract': {'$exists': True}, 'authors': {'$exists': True}}):
        for auth in entry['authors']:
            if 'page' not in auth.keys():
                continue 
            auth['page'] = auth['page'].replace('https://www.researchgate.net/', '').lower()
    
            if auth['page'] not in cur_auths:
                script = "insert into research_match.authors (auth_id, name, page, page_hash) VALUES (%i, '%s', '%s', %i)" % (nxt_auth, auth['name'].lower(), auth['page'], hash(auth['page']))
                script = script.replace("'NULL'", 'NULL')
                pg_insert(psql.client, script)
                cur_auths.add(auth['page'])
                nxt_auth += 1                
    



auth_dict = {k:v for k,v in pg_query(PSQL.client, 'select page_hash, auth_id from research_match.authors;').values}
pap_dict = {k:v for k,v in pg_query(PSQL.client, 'select mongo_hash, pap_id from research_match.papers;').values}
inst_dict = {k:v for k,v in pg_query(PSQL.client, 'select page_hash, inst_id from research_match.institutions;').values}
pub_dict = {k:v for k,v in pg_query(PSQL.client, 'select page_hash, pub_id from research_match.publishers;').values}

for entry in mongo.client.find({'abstract': {'$exists': True}}):
    








