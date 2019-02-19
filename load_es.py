import os, sys
try:                                            # if running in CLI
    cur_path = os.path.abspath(__file__)
except NameError:                               # if running in IDE
    cur_path = os.getcwd()

while cur_path.split('/')[-1] != 'research_match':
    cur_path = os.path.abspath(os.path.join(cur_path, os.pardir))    
sys.path.insert(1, os.path.join(cur_path, 'lib', 'python3.7', 'site-packages'))

import os, sys
from elasticsearch import Elasticsearch
import requests
import re
import string
from pymongo import MongoClient
import _config

mongodb_client = MongoClient(_config.mongodb_creds)
DB = mongodb_client['marine_science']


ES_INDEX_NAME = 'research_gate_1'
punc_remove = re.compile('[%s]' % re.escape(string.punctuation))

def load_es():
    res = requests.get('http://localhost:9200')

    print (res.content)
    es = Elasticsearch([{'host': 'localhost', 'port': '9200'}])
    
    if 'drop' in sys.argv:
        try:
            es.indices.delete(index=ES_INDEX_NAME, ignore=400)
            print('%s Successfully Dropped' % (ES_INDEX_NAME))
        except:
            pass
    es.indices.create(index=ES_INDEX_NAME, ignore=400)
    
    for entry in DB['research_gate'].find():
        id_name = entry['_id']
        entry.pop('_id')
        es.index(index=ES_INDEX_NAME, doc_type='test', id=id_name, body=entry)
        


   













#EXCLUDE_CONCEPTS = ['singles', 'billboard', 'want', 'money', 'banking', 'albums', 'films', 
#                    'good day', 'need', 'if you have to ask', 'that that is is', 'user',
#                    'bank', 'gratitude', 'aria charts', 'number', 'yeah yeah yeahs']
#EXCLUDE_CATEGORIES = ['art and entertainment', 'shows and events', 'society']
#EXCLUDE_KEY_WORDS = ['speaker', 'name', 'account', 'number', 'bank', 'today', 'day', 
#                     'dollars', 'sir', 'line', 'moment', 'call', 'question', 
#                     'financial institutions', 'good day', 'need', 'if you have to ask',
#                     'that that is is', 'user', 'bank']
#
#if True:
#    SPARK_OUTPUT = os.path.join(cur_path, 'spark_output')
#    COMBINED_OUTPUT = os.path.join(cur_path, 'spark_output', 'combined_output.csv')
#
#PROC_JSON = os.path.join(cur_path, 'processed_outputs')
#
#if not os.path.exists(SPARK_OUTPUT):
#    os.makedirs(SPARK_OUTPUT)
#       
#    
#def clear_staging(directory):    
#    for _file in os.listdir(directory):
#        os.remove(os.path.join(directory, _file))    






if __name__ == '__main__':    
    if 'load' in sys.argv:
        ES_INDEX_NAME = input('Please provide an INDEX NAME for elasticsearch:   ')
        load_es()
                





