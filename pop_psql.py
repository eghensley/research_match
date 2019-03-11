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
#from progress_bar import progress

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
        current_ = {k:v for v,k in _data.values}
        next_idx = np.max(_data[0]) + 1
    else:
        next_idx = 0
        current_ = {}
    return(next_idx, current_, _psql)
        

def _det_current_xref(_psql, field):
#    _psql, field = PSQL, 'xref_pap_inst'
    try:
        _data = pg_query(_psql.client, 'select %s_id from research_match.%s;' % (field.replace('xref_',''), field))
    except:
        _psql.reset_db_con()
        pg_create_table(_psql.client, field)
        _data = pg_query(_psql.client, 'select %s_id from research_match.%s;' % (field.replace('xref_',''), field))
    if len(_data) > 0:
        next_idx = np.max(_data[0]) + 1
    else:
        next_idx = 0
    return(next_idx, _psql)
    

def pop_pap(_psql, _nxt_pap, _cur_paps, _entry):
    script = "insert into research_match.papers (pap_id, mongo_hash, page, page_hash) VALUES (%i, '%s', '%s', %i)" % (_nxt_pap, str(_entry['_id']), _entry['url_tag'], hash(_entry['url_tag']))
    script = script.replace("'NULL'", 'NULL')
    pg_insert(_psql.client, script)
    _cur_paps[_entry['url_tag']] = _nxt_pap
    _nxt_pap += 1 
    return(_nxt_pap, _cur_paps)
    
def pop_pub(_psql, _nxt_pub, _nxt_pap, _cur_pubs, _entry):
    script = "insert into research_match.publishers (pub_id, name, page, page_hash) VALUES (%i, '%s', '%s', %i)" % (_nxt_pub, _entry['publisher']['name'].lower(), _entry['publisher']['page'], hash(_entry['publisher']['page']))
    pg_insert(_psql.client, script)
    _cur_pubs[_entry['publisher']['page']] = _nxt_pub
    _nxt_pub += 1      
    return(_nxt_pub, _cur_pubs)
 
def pop_pap_pub(_psql, _pub_id, _nxt_pap, _nxt_pap_pub):
    script = "insert into research_match.xref_pap_pub (pap_pub_id, pap_id, pub_id) VALUES (%i, %i, %i)" % (_nxt_pap_pub, _nxt_pap - 1, _pub_id)
    pg_insert(_psql.client, script)
    _nxt_pap_pub += 1      
    return(_nxt_pap_pub)

def pop_auth(_psql, _nxt_auth, _nxt_pap, _cur_auths, _auth):
    script = "insert into research_match.authors (auth_id, name, page, page_hash) VALUES (%i, '%s', '%s', %i)" % (_nxt_auth, _auth['name'].lower(), _auth['page'], hash(_auth['page']))
    script = script.replace("'NULL'", 'NULL')
    pg_insert(_psql.client, script)  
    _cur_auths[_auth['page']] = _nxt_auth
    _nxt_auth += 1 
    return(_nxt_auth, _cur_auths)                
                
def pop_pap_auth(_psql, _auth_id, _nxt_pap, _nxt_pap_auth):
    script = "insert into research_match.xref_pap_auth (pap_auth_id, pap_id, auth_id) VALUES (%i, %i, %i)" % (_nxt_pap_auth, _nxt_pap - 1, _auth_id)
    pg_insert(_psql.client, script)
    _nxt_pap_auth += 1    
    return(_nxt_pap_auth)
    
def pop_inst(_psql, _nxt_inst, _nxt_pap, _cur_insts, _inst):
    script = "insert into research_match.institutions (inst_id, name, page, page_hash) VALUES (%i, '%s', '%s', %i)" % (_nxt_inst, _inst['name'].lower(), _inst['page'], hash(_inst['page']))
    script = script.replace("'NULL'", 'NULL')
    pg_insert(_psql.client, script)
    _cur_insts[_inst['page']] = _nxt_inst
    _nxt_inst += 1  
    return(_nxt_inst, _cur_insts)                
        
def pop_pap_inst(_psql, _inst_id, _nxt_pap, _nxt_pap_inst):
    script = "insert into research_match.xref_pap_inst (pap_inst_id, pap_id, inst_id) VALUES (%i, %i, %i)" % (_nxt_pap_inst, _nxt_pap - 1, _inst_id)
    pg_insert(_psql.client, script)
    _nxt_pap_inst += 1      
    return(_nxt_pap_inst)         
      
    
def update_psql(mongo, psql):
    nxt_pap, cur_paps, psql = _det_current_(psql, 'papers')
    nxt_pub, cur_pubs, psql = _det_current_(psql, 'publishers')
    nxt_auth, cur_auths, psql = _det_current_(psql, 'authors')
    nxt_inst, cur_insts, psql = _det_current_(psql, 'institutions')
    
    nxt_pap_inst, psql = _det_current_xref(psql, 'xref_pap_inst')
    nxt_pap_pub, psql = _det_current_xref(psql, 'xref_pap_pub')
    nxt_pap_auth, psql = _det_current_xref(psql, 'xref_pap_auth')
    
    for entry in mongo.client.find({'abstract': {'$exists': True}}):
        entry['url_tag'] = entry['url_tag'].lower()
        if entry['url_tag'] not in cur_paps.keys():
            # Add papers
            nxt_pap, cur_paps = pop_pap(psql, nxt_pap, cur_paps, entry)
            
            # Add publishers
            if 'publisher' in entry.keys():
                entry['publisher']['page'] = entry['publisher']['page'].replace('https://www.researchgate.net/', '').lower()
                if entry['publisher']['page'] not in cur_pubs.keys():
                    nxt_pub, cur_pubs = pop_pub(psql, nxt_pub, nxt_pap, cur_pubs, entry)
                nxt_pap_pub = pop_pap_pub(psql, cur_pubs[entry['publisher']['page']], nxt_pap, nxt_pap_pub)
    #        # Add authors
            for auth in entry['authors']:
                if 'page' not in auth.keys():
                    continue 
                auth['page'] = auth['page'].replace('https://www.researchgate.net/', '').lower()
                if auth['page'] not in cur_auths:
                    nxt_auth, cur_auths = pop_auth(psql, nxt_auth, nxt_pap, cur_auths, auth)
                nxt_pap_auth = pop_pap_auth(psql, cur_auths[auth['page']], nxt_pap, nxt_pap_auth)
                # Add institutions
                if 'institution' in auth.keys():
                    inst = auth['institution']
                    if 'page' not in inst.keys():
                        continue   
                    inst['page'] = inst['page'].replace('https://www.researchgate.net/', '').lower()
                    if inst['page'] not in cur_insts.keys():
                        nxt_inst, cur_insts = pop_inst(psql, nxt_inst, nxt_pap, cur_insts, inst)
                    nxt_pap_inst = pop_pap_inst(psql, cur_insts[inst['page']], nxt_pap, nxt_pap_inst)


def update_refs(mongo, psql):
    nxt_pap, cur_paps, psql = _det_current_(psql, 'papers')
    pg_create_table(psql.client, 'references')
    nxt_ref = 0
    for entry in mongo.client.find({'abstract': {'$exists': True}}):
        if 'references' in entry.keys():
            entry['url_tag'] = entry['url_tag'].lower()
            for ref in entry['references']:
                if ref.lower() in cur_paps.keys():
                    script = "insert into research_match.references (ref_id, cit_pap_id, ref_pap_id) VALUES (%i, %i, %i)" % (nxt_ref, cur_paps[entry['url_tag']], cur_paps[ref.lower()])
                    pg_insert(psql.client, script)    
                    nxt_ref += 1
                    
                    
MONGO = _connections.db_connection('mongo')
PSQL = _connections.db_connection('psql')



                    
                
                
                
