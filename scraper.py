import os, sys
try:                                            # if running in CLI
    cur_path = os.path.abspath(__file__)
except NameError:                               # if running in IDE
    cur_path = os.getcwd()

while cur_path.split('/')[-1] != 'research_match':
    cur_path = os.path.abspath(os.path.join(cur_path, os.pardir))    
sys.path.insert(1, os.path.join(cur_path, 'lib', 'python3.7', 'site-packages'))

from lxml import html
import _config
import _connections
from watson_developer_cloud import NaturalLanguageUnderstandingV1
from watson_developer_cloud.natural_language_understanding_v1 import Features, KeywordsOptions, CategoriesOptions, ConceptsOptions
import unicodedata
import json
from random import randint
from time import sleep


nlu = NaturalLanguageUnderstandingV1(version=_config.nlu_credentials["version"], username=_config.nlu_credentials["username"],
                                        password=_config.nlu_credentials["password"])
nlu.set_default_headers({'x-watson-learning-opt-out' : "true"})


def strip_non_unicode(text):
    return(unicodedata.normalize("NFKD", text.replace("'", '')).encode('ascii','ignore').decode())
    
def process_scraped(data, exp_length = 1, min_len = False):
    if min_len:
        if len(data) < min_len:
            raise ValueError('Data not in expected format.')
        return([strip_non_unicode(i).strip() for i in data])
    else:
        if len(data) != exp_length:
            raise ValueError('Data not in expected format.')
        return(strip_non_unicode(data[0]).strip())
 
def store_abstracts(link, webbrowser, db):
#    link, webbrowser, db = p_link, browser, DB
#    link, webbrowser, db = prev_progress['error_link'], browser, DB
    
    webbrowser.get('https://www.researchgate.net/'+link)
    sleep(randint(10,100)/10)
    article_tree = html.fromstring(webbrowser.page_source)

    publication_data = {'url_tag': link}
    
    published = {}
    try:
        published['page'] = 'https://www.researchgate.net/' + process_scraped(article_tree.xpath('//div[@class="publication-meta"]/div/span/a/@href'))
        published['name'] = process_scraped(article_tree.xpath('//div[@class="publication-meta"]/div/span/a/text()'))
        published['reference'] = process_scraped(article_tree.xpath('//div[@class="publication-meta"]/div/span/text()')[:1])
        publication_data['publisher'] = published
        publication_data['date'] = process_scraped(article_tree.xpath('//div[@class="publication-meta"]/div/span/text()')[1:2]).replace('• ', '')
    except:
        try:
            publication_data['date'] = process_scraped(article_tree.xpath('//div[@class="publication-meta"]/div/span/text()')).replace('• ', '')
        except:
            pass

    try:
        publication_data['views'] = int(process_scraped([i for i in article_tree.xpath('//div[@class="publication-meta"]/div/text()') if 'read' in i.lower()]).split(' ')[0])
    except:
        pass
                   
    try:
        publication_data['doi'] = process_scraped(article_tree.xpath('//div[@class="publication-meta"]/div/a/text()'))
    except:
        pass
    
    page_authors = []
    pub_authors = article_tree.xpath('//*[@class="publication-details__section"]/ul/li/div/div/div/div/div[2]/div/div/div/div')
    for auth in pub_authors:
        author = {}
        author['name'] = process_scraped(auth.xpath('div/a/text()'))
        try:
            author['page'] = process_scraped(auth.xpath('ul/li[1]/span/a/@href'))
        except ValueError:
            pass
        institution = {}
        try:
            institution['name'] = process_scraped(auth.xpath('ul/li[2]/span/a/text()'))
        except ValueError:
            pass
        try:
            institution['page'] = 'https://www.researchgate.net/' + process_scraped(auth.xpath('ul/li[2]/span/a/@href'))
        except ValueError:
            pass
        if len(institution) > 0:
            author['institution'] = institution
        page_authors.append(author)
    publication_data['authors'] = page_authors

        
    pub_abstract = False
    for i in range(2,5):
        try:
            pub_abstract = process_scraped(article_tree.xpath('//*[@class="publication-details__section"]/div[%i]/div[2]/div/text()' % (i)))
            publication_data['abstract'] = {'text': pub_abstract}
            try: 
                nlu_output = nlu.analyze(text=pub_abstract, features = Features(keywords= KeywordsOptions(), categories=CategoriesOptions(), concepts = ConceptsOptions())).result
                abs_categories = nlu_output["categories"]
                abs_concepts = nlu_output["concepts"]
                abs_keywords = nlu_output["keywords"]
                publication_data['abstract']['nlu'] = {'categories':abs_categories, 'concepts': abs_concepts, 'keywords': abs_keywords}
            except:
                print('NLU Error')
                pass
            break
        except:
            pass
    
    db.client.insert_one(publication_data)

    return(webbrowser, db)
    
    
def next_page(web_url):
    return(web_url.split('&page=')[0] + '&page=' + str(int(web_url.split('&page=')[-1]) + 1))
    
    
def scrape():
    DB = _connections.db_connection('mongo')
    
    
    with open(os.path.join(cur_path, 'last_error.json')) as f:
        prev_progress = json.load(f)    
    
    url = prev_progress['last_page']
#    url = 'https://www.researchgate.net/search/publications?q=marine%2Bscience&page=1'
    
    browser = _connections.sel_scraper()
    
    while True:
        
        try:
            browser.get(url)#, headers=head)
            sleep(randint(10,100)/10)
            tree = html.fromstring(browser.page_source)
            
            paper_links = tree.xpath('//div[@class="react-container"]/div/div[2]/div[2]/div/div[2]/div/div[1]/div/div/div/div/div/div/div/div/div/div/a/@href')
            paper_links = [i.split('?')[0] for i in paper_links]
            
            if len(paper_links) == 0:
                raise ValueError()
                
        except:
            with open(os.path.join(cur_path, 'last_error.json'), 'w') as fp:
                json.dump({'last_page':url}, fp) 
            DB.disconnect()
            raise IndexError()
                                
        for p_link in paper_links:
            try:
                len(DB.client.find_one({'url_tag': p_link}))
                print('Article already archived, skipping')
            except:
                if 'book_review' in p_link.lower():
                    continue
                print(p_link)
                try:
                    browser, DB = store_abstracts(p_link, browser, DB)
                except:
                    print(p_link)
                    
                    with open(os.path.join(cur_path, 'last_error.json'), 'w') as fp:
                        json.dump({'error_link': p_link, 'last_page':url}, fp)                
                    DB.disconnect()
                    raise ValueError()
        url = next_page(url)


def see_all(_browser):
#    _browser = browser
    click_more = True
    while click_more:
        sleep(.25)
        try:
            see_more = _browser.find_elements_by_xpath('//div[@class="publication-citations__more"]/button')[-1]
        except IndexError:
            click_more = False
            break
        try:
            see_more.click()
        except Exception as e:
            print(e)
            pass


def load_ref_page(_browser):
    try:
        ref_tab = _browser.find_elements_by_xpath('//button[@class="nova-c-nav__item references js-lite-click"]')[-1]
        ref_tab.click()
    except:
        pass


def add_refs():
    DB = _connections.db_connection('mongo')
    browser = _connections.sel_scraper(headless = True)

    for doc in DB.client.find():
        if 'abstract' not in doc.keys():
            continue
        if 'references' in doc.keys():
            continue
        
        print(doc['url_tag'])
        url = 'https://www.researchgate.net/'+doc['url_tag']
        sleep(randint(10,100)/25)
        
        browser.get(url) 
        article_tree = html.fromstring(browser.page_source)
#        if len(article_tree.xpath('//button[@class="nova-c-nav__item is-selected references js-lite-click"]')) == 0:
        load_ref_page(browser)           
        see_all(browser)
        article_tree = html.fromstring(browser.page_source)
        references = article_tree.xpath('//div[@itemprop="citation"]/div/div/div/div/a/@href')    
        DB.client.update_one({'_id': doc['_id']}, {'$set': {'references': references}})
              
if __name__ == '__main__':
    add_refs()
